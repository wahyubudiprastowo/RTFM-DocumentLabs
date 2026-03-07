import csv
import fcntl
import json
import os
import random
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta, time as dtime
from typing import Dict, List, Optional, Set, Tuple

import requests

SPIN_RE = re.compile(r"\{\{\s*spintext\s*:\s*(.*?)\s*\}\}", re.IGNORECASE | re.DOTALL)
VAR_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")
DAY_KEYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

HTTP_SESSION = requests.Session()


# -----------------------
# .env loader
# -----------------------
def load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


def env_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_int(key: str, default: int = 0) -> int:
    v = os.environ.get(key, "")
    return int(v) if v != "" else default


def env_float(key: str, default: float = 0.0) -> float:
    v = os.environ.get(key, "")
    return float(v) if v != "" else default


def env_bool(key: str, default: bool = False) -> bool:
    v = os.environ.get(key, "")
    if v == "":
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_csv_items(value: str) -> List[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_csv_set(value: str) -> Set[str]:
    return {x.strip() for x in parse_csv_items(value)}


def now_dt() -> datetime:
    return datetime.now()


def now_iso() -> str:
    return now_dt().isoformat(timespec="seconds")


# -----------------------
# Text helpers
# -----------------------
def expand_spintext(text: str, rng: random.Random) -> str:
    while True:
        m = SPIN_RE.search(text)
        if not m:
            break
        options = [x.strip() for x in m.group(1).split("|") if x.strip()]
        choice = rng.choice(options) if options else ""
        text = text[:m.start()] + choice + text[m.end():]
    return text


def substitute_vars(text: str, row: Dict[str, str]) -> str:
    def repl(match: re.Match) -> str:
        key = match.group(1)
        return (row.get(key, "") or "").strip()
    return VAR_RE.sub(repl, text)


def normalize_message(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    cleaned = []
    for ln in lines:
        if ln == "" and cleaned and cleaned[-1] == "":
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).strip()


def normalize_phone(phone: str) -> str:
    p = (phone or "").strip()
    p = re.sub(r"[^\d+]", "", p)
    if p.startswith("+"):
        p = p[1:]
    if p.startswith("0"):
        p = "62" + p[1:]
    return p


def is_valid_phone(phone: str, min_len: int, max_len: int) -> bool:
    return phone.isdigit() and min_len <= len(phone) <= max_len


def short_text(value: str, max_len: int = 300) -> str:
    value = value or ""
    return value if len(value) <= max_len else value[:max_len] + "..."


# -----------------------
# File lock
# -----------------------
def acquire_file_lock(lock_path: str):
    os.makedirs(os.path.dirname(lock_path), exist_ok=True) if os.path.dirname(lock_path) else None
    fp = open(lock_path, "w")
    try:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fp.write(str(os.getpid()))
        fp.flush()
        return fp
    except BlockingIOError:
        fp.close()
        return None


def release_file_lock(fp) -> None:
    try:
        fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
    except Exception:
        pass
    try:
        fp.close()
    except Exception:
        pass


# -----------------------
# Scheduling
# -----------------------
def parse_hhmm(value: str) -> dtime:
    hh, mm = value.strip().split(":")
    return dtime(hour=int(hh), minute=int(mm))


def get_day_key(dt: datetime) -> str:
    return DAY_KEYS[dt.weekday()]


def parse_allowed_days(value: str) -> Set[str]:
    days = {x.strip().upper() for x in parse_csv_items(value)}
    return {d for d in days if d in DAY_KEYS}


def is_in_window(now: datetime, start_t: dtime, end_t: dtime) -> bool:
    cur = now.time()
    if start_t <= end_t:
        return start_t <= cur < end_t
    return cur >= start_t or cur < end_t


def get_business_window_for_day(day_key: str) -> Tuple[bool, Optional[dtime], Optional[dtime]]:
    enabled = env_bool(f"BUSINESS_{day_key}_ENABLED", False)
    if not enabled:
        return False, None, None
    start_s = env_str(f"BUSINESS_{day_key}_START")
    end_s = env_str(f"BUSINESS_{day_key}_END")
    if not start_s or not end_s:
        return False, None, None
    return True, parse_hhmm(start_s), parse_hhmm(end_s)


def is_send_allowed_now(now: datetime, campaign_allowed_days: Set[str]) -> bool:
    day_key = get_day_key(now)

    if campaign_allowed_days and day_key not in campaign_allowed_days:
        return False

    if not env_bool("BUSINESS_HOURS_ENABLED", False):
        return True

    enabled, start_t, end_t = get_business_window_for_day(day_key)
    if not enabled or not start_t or not end_t:
        return False

    return is_in_window(now, start_t, end_t)


def next_allowed_window_start(now: datetime, campaign_allowed_days: Set[str]) -> Optional[datetime]:
    business_enabled = env_bool("BUSINESS_HOURS_ENABLED", False)

    for add_days in range(0, 15):
        candidate_date = now.date() + timedelta(days=add_days)
        midnight = datetime.combine(candidate_date, dtime(0, 0))
        day_key = get_day_key(midnight)

        if campaign_allowed_days and day_key not in campaign_allowed_days:
            continue

        if business_enabled:
            day_enabled, start_t, end_t = get_business_window_for_day(day_key)
            if not day_enabled or not start_t or not end_t:
                continue
            start_dt = datetime.combine(candidate_date, start_t)

            if add_days == 0:
                if is_in_window(now, start_t, end_t):
                    return now
                if start_dt > now:
                    return start_dt
            else:
                return start_dt
        else:
            if add_days == 0:
                return now
            return midnight

    return None


def ensure_schedule_window_or_exit(campaign_allowed_days: Set[str]) -> bool:
    wait_for_window = env_bool("WAIT_FOR_WINDOW", False)
    now = now_dt()

    if is_send_allowed_now(now, campaign_allowed_days):
        return True

    next_start = next_allowed_window_start(now, campaign_allowed_days)
    if next_start is None:
        print("[WINDOW] no allowed sending window found from current config -> exit")
        return False

    secs = max(0, int((next_start - now).total_seconds()))
    if wait_for_window:
        print(
            f"[WINDOW] outside allowed schedule now={now.strftime('%Y-%m-%d %H:%M:%S')} "
            f"next={next_start.strftime('%Y-%m-%d %H:%M:%S')} wait={secs}s"
        )
        time.sleep(secs)
        return True

    print(
        f"[WINDOW] outside allowed schedule now={now.strftime('%Y-%m-%d %H:%M:%S')} "
        f"next={next_start.strftime('%Y-%m-%d %H:%M:%S')} -> exit"
    )
    return False


# -----------------------
# DB
# -----------------------
def db_connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA temp_store=MEMORY")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS recipients (
            phone TEXT PRIMARY KEY,
            name TEXT,
            opt_in TEXT,
            do_not_contact TEXT,
            extra_json TEXT,
            imported_at TEXT,
            updated_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_queue (
            phone TEXT,
            campaign_id TEXT,
            env_name TEXT,
            queued_at TEXT,
            status TEXT,
            attempts INTEGER DEFAULT 0,
            template_used TEXT,
            last_message TEXT,
            last_status_code INTEGER,
            last_response_text TEXT,
            last_attempt_at TEXT,
            sent_at TEXT,
            in_progress_by TEXT,
            in_progress_at TEXT,
            PRIMARY KEY(phone, campaign_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS send_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            campaign_id TEXT,
            env_name TEXT,
            attempt_no INTEGER,
            queue_status_before TEXT,
            result_status TEXT,
            status_code INTEGER,
            template_used TEXT,
            message TEXT,
            response_text TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_campaign_queue_status
        ON campaign_queue(campaign_id, env_name, status)
    """)
    conn.commit()
    return conn


def clean_dictreader_row(row: Dict) -> Dict[str, str]:
    clean: Dict[str, str] = {}
    for k, v in row.items():
        if not isinstance(k, str):
            continue
        k2 = k.strip()
        if not k2:
            continue
        if isinstance(v, str):
            clean[k2] = v.strip()
        elif v is None:
            clean[k2] = ""
        else:
            clean[k2] = str(v).strip()
    return clean


def import_csv_to_db(
    conn: sqlite3.Connection,
    csv_path: str,
    delimiter: str,
    phone_col: str,
    name_col: str,
    opt_in_col: str,
    dnc_col: str
) -> None:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter, restkey="__extra__", restval="")
        for raw in reader:
            row = clean_dictreader_row(raw)

            phone = normalize_phone(row.get(phone_col, ""))
            if not phone:
                continue

            name = row.get(name_col, "")
            opt_in = row.get(opt_in_col, "")
            dnc = row.get(dnc_col, "")

            extras = dict(row)
            for key in (phone_col, name_col, opt_in_col, dnc_col):
                extras.pop(key, None)
            extras.pop("__extra__", None)

            ts = now_iso()
            conn.execute("""
                INSERT INTO recipients (phone, name, opt_in, do_not_contact, extra_json, imported_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(phone) DO UPDATE SET
                    name=excluded.name,
                    opt_in=excluded.opt_in,
                    do_not_contact=excluded.do_not_contact,
                    extra_json=excluded.extra_json,
                    updated_at=excluded.updated_at
            """, (phone, name, opt_in, dnc, json.dumps(extras, ensure_ascii=False), ts, ts))
    conn.commit()


def is_truthy(value: str, truth_set: Set[str]) -> bool:
    return (value or "").strip().lower() in truth_set


def iter_eligible_recipients(
    conn: sqlite3.Connection,
    opt_in_true: Set[str],
    dnc_true: Set[str]
) -> List[Dict[str, str]]:
    cur = conn.cursor()
    cur.execute("SELECT phone, name, opt_in, do_not_contact, extra_json FROM recipients")
    rows = cur.fetchall()

    results: List[Dict[str, str]] = []
    for row in rows:
        opt_in = row["opt_in"] or ""
        dnc = row["do_not_contact"] or ""
        if not is_truthy(opt_in, opt_in_true):
            continue
        if is_truthy(dnc, dnc_true):
            continue

        extras = {}
        if row["extra_json"]:
            try:
                extras = json.loads(row["extra_json"])
            except Exception:
                extras = {}

        item = {
            "phone": row["phone"],
            "name": row["name"] or "",
            "opt_in": opt_in,
            "do_not_contact": dnc
        }
        for k, v in extras.items():
            item[str(k)] = "" if v is None else str(v)
        results.append(item)

    return results


def prepare_campaign_queue(
    conn: sqlite3.Connection,
    campaign_id: str,
    env_name: str,
    opt_in_true: Set[str],
    dnc_true: Set[str]
) -> int:
    eligible = iter_eligible_recipients(conn, opt_in_true, dnc_true)
    inserted = 0
    ts = now_iso()

    for row in eligible:
        cur = conn.execute("""
            INSERT OR IGNORE INTO campaign_queue
            (phone, campaign_id, env_name, queued_at, status, attempts)
            VALUES (?, ?, ?, ?, 'PENDING', 0)
        """, (row["phone"], campaign_id, env_name, ts))
        inserted += cur.rowcount

    conn.commit()
    return inserted


def recover_stale_locks(conn: sqlite3.Connection, stale_minutes: int) -> int:
    cutoff = (now_dt() - timedelta(minutes=stale_minutes)).isoformat(timespec="seconds")
    cur = conn.execute("""
        UPDATE campaign_queue
        SET status='PENDING',
            in_progress_by=NULL,
            in_progress_at=NULL
        WHERE status='IN_PROGRESS'
          AND in_progress_at IS NOT NULL
          AND in_progress_at <= ?
    """, (cutoff,))
    conn.commit()
    return cur.rowcount


def set_queue_status(
    conn: sqlite3.Connection,
    phone: str,
    campaign_id: str,
    status: str,
    response_text: str = ""
) -> None:
    conn.execute("""
        UPDATE campaign_queue
        SET status=?,
            last_response_text=CASE
                WHEN ? <> '' THEN ?
                ELSE last_response_text
            END,
            in_progress_by=NULL,
            in_progress_at=NULL
        WHERE phone=? AND campaign_id=?
    """, (status, response_text, response_text[:2000], phone, campaign_id))
    conn.commit()


def acquire_queue_lock(
    conn: sqlite3.Connection,
    phone: str,
    campaign_id: str,
    run_id: str
) -> bool:
    ts = now_iso()
    cur = conn.execute("""
        UPDATE campaign_queue
        SET status='IN_PROGRESS',
            in_progress_by=?,
            in_progress_at=?
        WHERE phone=?
          AND campaign_id=?
          AND status IN ('PENDING', 'FAILED')
    """, (run_id, ts, phone, campaign_id))
    conn.commit()
    return cur.rowcount == 1


def release_queue_lock_back_to_pending(
    conn: sqlite3.Connection,
    phone: str,
    campaign_id: str
) -> None:
    conn.execute("""
        UPDATE campaign_queue
        SET status='PENDING',
            in_progress_by=NULL,
            in_progress_at=NULL
        WHERE phone=? AND campaign_id=? AND status='IN_PROGRESS'
    """, (phone, campaign_id))
    conn.commit()


def update_queue_result(
    conn: sqlite3.Connection,
    phone: str,
    campaign_id: str,
    result_status: str,
    template_used: str,
    message: str,
    status_code: int,
    response_text: str
) -> None:
    ts = now_iso()
    sent_at = ts if result_status == "SENT" else None

    conn.execute("""
        UPDATE campaign_queue
        SET status=?,
            attempts=attempts+1,
            template_used=?,
            last_message=?,
            last_status_code=?,
            last_response_text=?,
            last_attempt_at=?,
            sent_at=COALESCE(?, sent_at),
            in_progress_by=NULL,
            in_progress_at=NULL
        WHERE phone=? AND campaign_id=?
    """, (
        result_status,
        template_used,
        message,
        status_code,
        response_text[:2000],
        ts,
        sent_at,
        phone,
        campaign_id
    ))
    conn.commit()


def record_send_attempt(
    conn: sqlite3.Connection,
    phone: str,
    campaign_id: str,
    env_name: str,
    attempt_no: int,
    queue_status_before: str,
    result_status: str,
    status_code: int,
    template_used: str,
    message: str,
    response_text: str
) -> None:
    conn.execute("""
        INSERT INTO send_attempts
        (phone, campaign_id, env_name, attempt_no, queue_status_before, result_status,
         status_code, template_used, message, response_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        phone,
        campaign_id,
        env_name,
        attempt_no,
        queue_status_before,
        result_status,
        status_code,
        template_used,
        message,
        response_text[:2000],
        now_iso()
    ))
    conn.commit()


def get_queue_counts(conn: sqlite3.Connection, campaign_id: str, env_name: str) -> Dict[str, int]:
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*) AS total
        FROM campaign_queue
        WHERE campaign_id=? AND env_name=?
        GROUP BY status
    """, (campaign_id, env_name))
    counts = {row["status"]: int(row["total"]) for row in cur.fetchall()}
    return counts


def print_queue_summary(conn: sqlite3.Connection, campaign_id: str, env_name: str) -> None:
    counts = get_queue_counts(conn, campaign_id, env_name)
    print(f"[SUMMARY] campaign={campaign_id} env={env_name}")
    if not counts:
        print("  no queue rows")
        return
    total_all = 0
    for status in sorted(counts.keys()):
        print(f"  {status}: {counts[status]}")
        total_all += counts[status]
    print(f"  TOTAL: {total_all}")


def pick_queue_items(
    conn: sqlite3.Connection,
    campaign_id: str,
    env_name: str,
    limit: int,
    max_attempts: int,
    retry_failed: bool,
    opt_in_true: Set[str],
    dnc_true: Set[str]
) -> List[Dict[str, str]]:
    statuses = ["PENDING"]
    if retry_failed:
        statuses.append("FAILED")

    placeholders = ",".join("?" for _ in statuses)
    sql = f"""
        SELECT
            q.phone,
            q.status,
            q.attempts,
            q.last_attempt_at,
            q.last_status_code,
            q.last_response_text,
            r.name,
            r.opt_in,
            r.do_not_contact,
            r.extra_json
        FROM campaign_queue q
        JOIN recipients r ON r.phone = q.phone
        WHERE q.campaign_id = ?
          AND q.env_name = ?
          AND q.status IN ({placeholders})
          AND q.attempts < ?
        ORDER BY
          CASE q.status WHEN 'PENDING' THEN 0 ELSE 1 END,
          q.attempts ASC,
          COALESCE(q.last_attempt_at, q.queued_at) ASC
        LIMIT ?
    """
    params = [campaign_id, env_name, *statuses, max_attempts, limit]
    cur = conn.cursor()
    cur.execute(sql, params)

    results: List[Dict[str, str]] = []
    for row in cur.fetchall():
        opt_in = row["opt_in"] or ""
        dnc = row["do_not_contact"] or ""
        if not is_truthy(opt_in, opt_in_true):
            continue
        if is_truthy(dnc, dnc_true):
            continue

        extras = {}
        if row["extra_json"]:
            try:
                extras = json.loads(row["extra_json"])
            except Exception:
                extras = {}

        item = {
            "phone": row["phone"],
            "name": row["name"] or "",
            "queue_status": row["status"],
            "attempts": int(row["attempts"] or 0),
            "last_attempt_at": row["last_attempt_at"] or "",
            "last_status_code": str(row["last_status_code"] or ""),
            "last_response_text": row["last_response_text"] or "",
        }
        for k, v in extras.items():
            item[str(k)] = "" if v is None else str(v)
        results.append(item)

    return results


# -----------------------
# Permanent fail / blacklist
# -----------------------
def load_blacklist() -> Set[str]:
    if not env_bool("BLACKLIST_ENABLED", False):
        return set()

    file_path = env_str("BLACKLIST_FILE")
    if not file_path or not os.path.exists(file_path):
        print(f"[BLACKLIST] file not found or empty: {file_path}")
        return set()

    file_type = env_str("BLACKLIST_FILE_TYPE", "auto").strip().lower()
    if file_type == "auto":
        _, ext = os.path.splitext(file_path.lower())
        file_type = "csv" if ext == ".csv" else "txt"

    numbers: Set[str] = set()

    if file_type == "csv":
        delimiter = env_str("BLACKLIST_CSV_DELIMITER", ";")
        column = env_str("BLACKLIST_CSV_COLUMN", "phone")
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                phone = normalize_phone((row.get(column, "") or "").strip())
                if phone:
                    numbers.add(phone)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        for token in re.split(r"[\n,;]+", content):
            phone = normalize_phone(token.strip())
            if phone:
                numbers.add(phone)

    print(f"[BLACKLIST] loaded={len(numbers)} from {file_path}")
    return numbers


def parse_permfail_http_codes() -> Set[int]:
    values = parse_csv_items(env_str("PERMFAIL_HTTP_CODES"))
    result = set()
    for v in values:
        try:
            result.add(int(v))
        except ValueError:
            pass
    return result


def parse_permfail_error_substrings() -> List[str]:
    return [x.lower() for x in parse_csv_items(env_str("PERMFAIL_ERROR_SUBSTRINGS"))]


def is_permanent_failure(
    status_code: int,
    response_text: str,
    perm_http_codes: Set[int],
    perm_substrings: List[str]
) -> bool:
    if status_code in perm_http_codes:
        return True

    body = (response_text or "").lower()
    for needle in perm_substrings:
        if needle and needle in body:
            return True
    return False


def mark_historical_permanent_failures(
    conn: sqlite3.Connection,
    campaign_id: str,
    env_name: str,
    perm_http_codes: Set[int],
    perm_substrings: List[str]
) -> int:
    cur = conn.cursor()
    cur.execute("""
        SELECT phone, last_status_code, last_response_text
        FROM campaign_queue
        WHERE campaign_id=?
          AND env_name=?
          AND status='FAILED'
    """, (campaign_id, env_name))
    rows = cur.fetchall()

    changed = 0
    for row in rows:
        status_code = int(row["last_status_code"] or 0)
        response_text = row["last_response_text"] or ""
        if is_permanent_failure(status_code, response_text, perm_http_codes, perm_substrings):
            conn.execute("""
                UPDATE campaign_queue
                SET status='SKIPPED_PERMFAIL'
                WHERE phone=? AND campaign_id=?
            """, (row["phone"], campaign_id))
            changed += 1

    conn.commit()
    return changed


# -----------------------
# Templates
# -----------------------
def load_template_specs(specs_csv: str) -> List[Dict[str, object]]:
    specs = [x.strip() for x in specs_csv.split(",") if x.strip()]
    templates: List[Dict[str, object]] = []

    for item in specs:
        if ":" in item:
            path, weight_str = item.rsplit(":", 1)
            path = path.strip()
            weight = int(weight_str.strip())
        else:
            path = item.strip()
            weight = 1

        with open(path, "r", encoding="utf-8") as f:
            templates.append({
                "path": path,
                "text": f.read().strip(),
                "weight": max(1, weight)
            })

    if not templates:
        raise SystemExit("No templates found. Set TEMPLATE_SPECS in .env")

    return templates


def choose_template(
    templates: List[Dict[str, object]],
    selection_mode: str,
    idx: int,
    attempt_no: int,
    rng: random.Random
) -> Tuple[str, str, int]:
    mode = (selection_mode or "weighted_random").strip().lower()

    if mode == "round_robin":
        pos = (idx - 1 + max(0, attempt_no - 1)) % len(templates)
        t = templates[pos]
        return str(t["path"]), str(t["text"]), int(t["weight"])

    if mode == "random":
        t = rng.choice(templates)
        return str(t["path"]), str(t["text"]), int(t["weight"])

    weights = [int(t["weight"]) for t in templates]
    t = rng.choices(templates, weights=weights, k=1)[0]
    return str(t["path"]), str(t["text"]), int(t["weight"])


# -----------------------
# HTTP helper
# -----------------------
def request_post_json(
    url: str,
    headers: Dict[str, str],
    payload: Dict,
    timeout_s: int,
    retry_count: int,
    retry_backoff_s: float
) -> Tuple[int, str]:
    attempt = 0
    last_err: Optional[str] = None

    while attempt <= retry_count:
        try:
            resp = HTTP_SESSION.post(url, headers=headers, json=payload, timeout=timeout_s)

            if (resp.status_code == 429 or 500 <= resp.status_code < 600) and attempt < retry_count:
                time.sleep(retry_backoff_s * (attempt + 1))
                attempt += 1
                continue

            return resp.status_code, resp.text

        except requests.RequestException as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < retry_count:
                time.sleep(retry_backoff_s * (attempt + 1))
                attempt += 1
                continue
            return 0, last_err or "REQUEST_EXCEPTION"

    return 0, last_err or "UNKNOWN_ERROR"


# -----------------------
# Evolution API
# -----------------------
def evolution_send_presence(
    base_url: str,
    api_key: str,
    instance: str,
    number: str,
    presence_type: str,
    delay_ms: int,
    timeout_s: int,
    retry_count: int,
    retry_backoff_s: float
) -> Tuple[int, str]:
    url = f"{base_url.rstrip('/')}/chat/sendPresence/{instance}"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "number": number,
        "options": {
            "delay": delay_ms,
            "presence": presence_type,
            "number": number
        }
    }
    return request_post_json(url, headers, payload, timeout_s, retry_count, retry_backoff_s)


def evolution_send_text(
    base_url: str,
    api_key: str,
    instance: str,
    number: str,
    message: str,
    delay_ms: int,
    link_preview: bool,
    timeout_s: int,
    retry_count: int,
    retry_backoff_s: float
) -> Tuple[int, str]:
    url = f"{base_url.rstrip('/')}/message/sendText/{instance}"
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "number": number,
        "text": message,
        "delay": delay_ms,
        "linkPreview": link_preview
    }
    return request_post_json(url, headers, payload, timeout_s, retry_count, retry_backoff_s)


# -----------------------
# Logging / export / report
# -----------------------
def append_log_csv(log_path: str, row: Dict[str, str]) -> None:
    exists = os.path.exists(log_path)
    headers = [
        "ts", "phone", "name", "campaign_id", "env_name", "template",
        "template_weight", "queue_status_before", "result_status", "attempt_no",
        "status_code", "success"
    ]
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in headers})


def export_failed_list(conn: sqlite3.Connection, campaign_id: str, env_name: str) -> Optional[str]:
    if not env_bool("FAILED_EXPORT_AUTO", False):
        return None

    base_path = env_str("FAILED_EXPORT_CSV")
    if not base_path:
        return None

    statuses = parse_csv_set(env_str("FAILED_EXPORT_STATUSES"))
    if not statuses:
        statuses = {"FAILED"}

    final_path = base_path
    if env_bool("FAILED_EXPORT_TIMESTAMPED", True):
        root, ext = os.path.splitext(base_path)
        ext = ext or ".csv"
        final_path = f"{root}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"

    placeholders = ",".join("?" for _ in statuses)
    sql = f"""
        SELECT
            q.phone,
            r.name,
            q.status,
            q.attempts,
            q.last_status_code,
            q.last_response_text,
            q.last_attempt_at,
            q.sent_at,
            q.template_used
        FROM campaign_queue q
        LEFT JOIN recipients r ON r.phone = q.phone
        WHERE q.campaign_id=?
          AND q.env_name=?
          AND q.status IN ({placeholders})
        ORDER BY q.status, q.phone
    """
    params = [campaign_id, env_name, *sorted(statuses)]
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()

    with open(final_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "phone", "name", "status", "attempts", "last_status_code",
                "last_response_text", "last_attempt_at", "sent_at", "template_used"
            ]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "phone": row["phone"],
                "name": row["name"] or "",
                "status": row["status"] or "",
                "attempts": row["attempts"] or 0,
                "last_status_code": row["last_status_code"] or "",
                "last_response_text": row["last_response_text"] or "",
                "last_attempt_at": row["last_attempt_at"] or "",
                "sent_at": row["sent_at"] or "",
                "template_used": row["template_used"] or "",
            })

    return final_path


def build_summary_text(
    conn: sqlite3.Connection,
    campaign_id: str,
    env_name: str,
    run_id: str,
    processed_count: int,
    failed_export_path: Optional[str]
) -> str:
    counts = get_queue_counts(conn, campaign_id, env_name)
    keys = sorted(counts.keys())

    lines = [
        "Evolution Broadcast Summary",
        f"run_id: {run_id}",
        f"campaign: {campaign_id}",
        f"env: {env_name}",
        f"processed_this_run: {processed_count}",
    ]
    for k in keys:
        lines.append(f"{k}: {counts[k]}")
    if failed_export_path:
        lines.append(f"failed_export: {failed_export_path}")
    return "\n".join(lines)


def send_telegram_report(text: str) -> None:
    if not env_bool("REPORT_TELEGRAM_ENABLED", False):
        return

    token = env_str("REPORT_TELEGRAM_BOT_TOKEN")
    chat_id = env_str("REPORT_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[REPORT] Telegram enabled but token/chat_id empty")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000]
    }
    try:
        resp = HTTP_SESSION.post(url, json=payload, timeout=20)
        print(f"[REPORT] Telegram status={resp.status_code}")
    except Exception as e:
        print(f"[REPORT] Telegram error={e}")


def send_discord_report(text: str) -> None:
    if not env_bool("REPORT_DISCORD_ENABLED", False):
        return

    webhook_url = env_str("REPORT_DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[REPORT] Discord enabled but webhook empty")
        return

    payload = {"content": text[:1800]}
    try:
        resp = HTTP_SESSION.post(webhook_url, json=payload, timeout=20)
        print(f"[REPORT] Discord status={resp.status_code}")
    except Exception as e:
        print(f"[REPORT] Discord error={e}")


# -----------------------
# Main
# -----------------------
def main() -> None:
    env_file = os.environ.get("ENV_FILE", ".env")
    load_dotenv(env_file)

    # lock first
    lock_path = env_str("LOCK_FILE_PATH")
    lock_fp = acquire_file_lock(lock_path)
    if lock_fp is None:
        raise SystemExit(f"Another run is already active. lock={lock_path}")

    try:
        # Evolution
        base_url = env_str("EVO_BASE_URL")
        api_key = env_str("EVO_API_KEY")
        instance = env_str("EVO_INSTANCE")
        if not base_url or not api_key or not instance:
            raise SystemExit("Missing EVO_BASE_URL / EVO_API_KEY / EVO_INSTANCE in .env")

        # General
        env_name = env_str("ENV_NAME")
        campaign_id = env_str("CAMPAIGN_ID")
        run_id = f"run-{int(time.time())}"
        campaign_allowed_days = parse_allowed_days(env_str("CAMPAIGN_ALLOWED_DAYS"))

        if not env_name or not campaign_id:
            raise SystemExit("Missing ENV_NAME / CAMPAIGN_ID in .env")

        # Files / DB
        contacts_csv = env_str("CONTACTS_CSV")
        delimiter = env_str("CSV_DELIMITER")
        db_path = env_str("DB_PATH")
        log_csv = env_str("LOG_CSV")
        if not contacts_csv or not delimiter or not db_path or not log_csv:
            raise SystemExit("Missing CONTACTS_CSV / CSV_DELIMITER / DB_PATH / LOG_CSV in .env")

        # Safety
        dry_run = env_bool("DRY_RUN", True)
        enable_sending = env_bool("ENABLE_SENDING", False)

        # Eligibility
        phone_col = env_str("PHONE_COLUMN")
        name_col = env_str("NAME_COLUMN")
        opt_in_col = env_str("OPT_IN_COLUMN")
        dnc_col = env_str("DNC_COLUMN")
        opt_in_true = {x.lower() for x in parse_csv_set(env_str("OPT_IN_TRUE"))}
        dnc_true = {x.lower() for x in parse_csv_set(env_str("DNC_TRUE"))}
        phone_min_len = env_int("PHONE_MIN_LEN")
        phone_max_len = env_int("PHONE_MAX_LEN")

        # Template
        template_selection = env_str("TEMPLATE_SELECTION")
        template_specs = env_str("TEMPLATE_SPECS")
        templates = load_template_specs(template_specs)

        # Evolution behavior
        request_timeout_s = env_int("REQUEST_TIMEOUT_S")
        http_retry_count = env_int("HTTP_RETRY_COUNT")
        http_retry_backoff_s = env_float("HTTP_RETRY_BACKOFF_S")
        evo_sendtext_delay_ms = env_int("EVO_SENDTEXT_DELAY_MS")
        evo_link_preview = env_bool("EVO_LINK_PREVIEW", False)
        evo_use_presence = env_bool("EVO_USE_PRESENCE", False)
        evo_presence_type = env_str("EVO_PRESENCE_TYPE")
        evo_presence_delay_ms = env_int("EVO_PRESENCE_DELAY_MS")
        evo_post_presence_sleep_s = env_float("EVO_POST_PRESENCE_SLEEP_S")

        # Queue / retry
        max_attempts = env_int("MAX_ATTEMPTS")
        retry_failed = env_bool("RETRY_FAILED", True)
        lock_stale_minutes = env_int("LOCK_STALE_MINUTES")
        perm_http_codes = parse_permfail_http_codes()
        perm_substrings = parse_permfail_error_substrings()

        # Pacing
        per_min = env_int("PER_MSG_MIN_S")
        per_max = env_int("PER_MSG_MAX_S")
        batch_size_min = env_int("BATCH_SIZE_MIN")
        batch_size_max = env_int("BATCH_SIZE_MAX")
        batch_min = env_int("BATCH_MIN_S")
        batch_max = env_int("BATCH_MAX_S")
        max_per_run = env_int("MAX_PER_RUN")

        conn = db_connect(db_path)
        cmd = sys.argv[1] if len(sys.argv) > 1 else "send"

        if cmd == "import":
            import_csv_to_db(conn, contacts_csv, delimiter, phone_col, name_col, opt_in_col, dnc_col)
            print(f"[OK] Imported CSV -> DB ({contacts_csv} -> {db_path})")
            return

        if cmd == "summary":
            print_queue_summary(conn, campaign_id, env_name)
            return

        if cmd == "export_failed":
            export_path = export_failed_list(conn, campaign_id, env_name)
            print(f"[OK] failed export: {export_path}")
            return

        if cmd != "send":
            raise SystemExit("Usage: python3 broadcast.py [import|summary|send|export_failed]")

        import_csv_to_db(conn, contacts_csv, delimiter, phone_col, name_col, opt_in_col, dnc_col)

        inserted = prepare_campaign_queue(conn, campaign_id, env_name, opt_in_true, dnc_true)
        recovered = recover_stale_locks(conn, lock_stale_minutes)
        hist_perm_skipped = mark_historical_permanent_failures(
            conn, campaign_id, env_name, perm_http_codes, perm_substrings
        )
        blacklist_numbers = load_blacklist()

        print(f"[INFO] run_id={run_id}")
        print(f"[INFO] env={env_name} campaign={campaign_id}")
        print(f"[INFO] dry_run={dry_run} enable_sending={enable_sending}")
        print(f"[INFO] queue_inserted={inserted} recovered_stale_locks={recovered} permfail_marked={hist_perm_skipped}")
        print(f"[INFO] instance={instance} base_url={base_url}")
        print(f"[INFO] template_selection={template_selection} template_count={len(templates)}")
        print(f"[INFO] max_attempts={max_attempts} retry_failed={retry_failed}")
        print(f"[INFO] per_message_pause={per_min}-{per_max}s")
        print(f"[INFO] batch_every={batch_size_min}-{batch_size_max} msgs")
        print(f"[INFO] batch_pause={batch_min}-{batch_max}s")
        print(f"[INFO] campaign_allowed_days={','.join(sorted(campaign_allowed_days)) or 'ALL'}")

        if not ensure_schedule_window_or_exit(campaign_allowed_days):
            return

        queue_items = pick_queue_items(
            conn=conn,
            campaign_id=campaign_id,
            env_name=env_name,
            limit=max_per_run,
            max_attempts=max_attempts,
            retry_failed=retry_failed,
            opt_in_true=opt_in_true,
            dnc_true=dnc_true
        )

        print(f"[INFO] eligible_queue_to_process={len(queue_items)} (max_per_run={max_per_run})")
        if not queue_items:
            print_queue_summary(conn, campaign_id, env_name)
            failed_export = export_failed_list(conn, campaign_id, env_name)
            summary_text = build_summary_text(conn, campaign_id, env_name, run_id, 0, failed_export)
            send_telegram_report(summary_text)
            send_discord_report(summary_text)
            return

        rng = random.Random()
        processed_count = 0
        sent_or_dryrun_count = 0
        processed_since_batch = 0
        next_batch_after = rng.randint(batch_size_min, batch_size_max)
        print(f"[INFO] first_batch_after={next_batch_after} messages")

        for idx, item in enumerate(queue_items, start=1):
            if not ensure_schedule_window_or_exit(campaign_allowed_days):
                print("[STOP] leaving run because outside schedule window")
                break

            phone = normalize_phone(item.get("phone", ""))
            name = item.get("name", "")
            queue_status_before = item.get("queue_status", "PENDING")
            previous_attempts = int(item.get("attempts", 0))
            next_attempt_no = previous_attempts + 1

            if not phone or not is_valid_phone(phone, phone_min_len, phone_max_len):
                print(f"[SKIP #{idx}] invalid phone={phone} name={name}")
                set_queue_status(conn, phone, campaign_id, "SKIPPED_PERMFAIL", "INVALID_PHONE")
                record_send_attempt(
                    conn, phone, campaign_id, env_name, next_attempt_no,
                    queue_status_before, "SKIPPED_PERMFAIL", 0, "", "", "INVALID_PHONE"
                )
                processed_count += 1
                continue

            if phone in blacklist_numbers:
                print(f"[SKIP #{idx}] blacklisted phone={phone} name={name}")
                set_queue_status(conn, phone, campaign_id, "SKIPPED_BLACKLIST", "BLACKLIST_MATCH")
                record_send_attempt(
                    conn, phone, campaign_id, env_name, previous_attempts,
                    queue_status_before, "SKIPPED_BLACKLIST", 0, "", "", "BLACKLIST_MATCH"
                )
                append_log_csv(log_csv, {
                    "ts": now_iso(),
                    "phone": phone,
                    "name": name,
                    "campaign_id": campaign_id,
                    "env_name": env_name,
                    "template": "",
                    "template_weight": "",
                    "queue_status_before": queue_status_before,
                    "result_status": "SKIPPED_BLACKLIST",
                    "attempt_no": str(previous_attempts),
                    "status_code": "0",
                    "success": "0",
                })
                processed_count += 1
                continue

            template_path, template_text, template_weight = choose_template(
                templates=templates,
                selection_mode=template_selection,
                idx=idx,
                attempt_no=next_attempt_no,
                rng=rng
            )
            msg = expand_spintext(template_text, rng)
            msg = substitute_vars(msg, item)
            msg = normalize_message(msg)

            if not msg:
                print(f"[SKIP #{idx}] empty message phone={phone} name={name}")
                set_queue_status(conn, phone, campaign_id, "SKIPPED_PERMFAIL", "EMPTY_MESSAGE")
                record_send_attempt(
                    conn, phone, campaign_id, env_name, next_attempt_no,
                    queue_status_before, "SKIPPED_PERMFAIL", 0, template_path, "", "EMPTY_MESSAGE"
                )
                processed_count += 1
                continue

            print(
                f"[QUEUE #{idx}/{len(queue_items)}] "
                f"phone={phone} name={name} "
                f"queue_status={queue_status_before} next_attempt={next_attempt_no} "
                f"template={template_path} weight={template_weight}"
            )

            did_message = False

            if dry_run or not enable_sending:
                print(f"\n--- DRY/LOCK #{idx} -> {phone} ({name}) template={template_path} weight={template_weight} ---\n{msg}\n")
                status_code = 0
                resp_text = "DRY_RUN_OR_DISABLED"
                result_status = "DRY_RUN"
                success = 1

                record_send_attempt(
                    conn=conn,
                    phone=phone,
                    campaign_id=campaign_id,
                    env_name=env_name,
                    attempt_no=next_attempt_no,
                    queue_status_before=queue_status_before,
                    result_status=result_status,
                    status_code=status_code,
                    template_used=template_path,
                    message=msg,
                    response_text=resp_text
                )
                did_message = True
            else:
                locked = acquire_queue_lock(conn, phone, campaign_id, run_id)
                if not locked:
                    print(f"[SKIP #{idx}] failed to lock queue phone={phone} name={name}")
                    continue

                try:
                    if evo_use_presence:
                        p_status, p_resp = evolution_send_presence(
                            base_url=base_url,
                            api_key=api_key,
                            instance=instance,
                            number=phone,
                            presence_type=evo_presence_type,
                            delay_ms=evo_presence_delay_ms,
                            timeout_s=request_timeout_s,
                            retry_count=http_retry_count,
                            retry_backoff_s=http_retry_backoff_s
                        )
                        print(f"[PRESENCE #{idx}] phone={phone} name={name} status={p_status}")
                        if p_status and not (200 <= p_status < 300):
                            print(f"[PRESENCE RESP] {short_text(p_resp, 300)}")
                        if evo_post_presence_sleep_s > 0:
                            time.sleep(evo_post_presence_sleep_s)

                    status_code, resp_text = evolution_send_text(
                        base_url=base_url,
                        api_key=api_key,
                        instance=instance,
                        number=phone,
                        message=msg,
                        delay_ms=evo_sendtext_delay_ms,
                        link_preview=evo_link_preview,
                        timeout_s=request_timeout_s,
                        retry_count=http_retry_count,
                        retry_backoff_s=http_retry_backoff_s
                    )

                    success = 1 if 200 <= status_code < 300 else 0
                    if success:
                        result_status = "SENT"
                    else:
                        result_status = (
                            "SKIPPED_PERMFAIL"
                            if is_permanent_failure(status_code, resp_text, perm_http_codes, perm_substrings)
                            else "FAILED"
                        )

                    update_queue_result(
                        conn=conn,
                        phone=phone,
                        campaign_id=campaign_id,
                        result_status=result_status,
                        template_used=template_path,
                        message=msg,
                        status_code=status_code,
                        response_text=resp_text
                    )

                    record_send_attempt(
                        conn=conn,
                        phone=phone,
                        campaign_id=campaign_id,
                        env_name=env_name,
                        attempt_no=next_attempt_no,
                        queue_status_before=queue_status_before,
                        result_status=result_status,
                        status_code=status_code,
                        template_used=template_path,
                        message=msg,
                        response_text=resp_text
                    )

                    print(
                        f"[SEND #{idx}] phone={phone} name={name} "
                        f"http={status_code} result={result_status} attempt={next_attempt_no}"
                    )
                    if not success:
                        print(f"[RESP] {short_text(resp_text, 500)}")

                    did_message = True

                except Exception as e:
                    err_text = f"{type(e).__name__}: {e}"
                    release_queue_lock_back_to_pending(conn, phone, campaign_id)

                    record_send_attempt(
                        conn=conn,
                        phone=phone,
                        campaign_id=campaign_id,
                        env_name=env_name,
                        attempt_no=next_attempt_no,
                        queue_status_before=queue_status_before,
                        result_status="EXCEPTION_UNLOCKED",
                        status_code=0,
                        template_used=template_path,
                        message=msg,
                        response_text=err_text
                    )

                    print(f"[EXCEPTION #{idx}] phone={phone} name={name} err={err_text}")
                    processed_count += 1
                    continue

            append_log_csv(log_csv, {
                "ts": now_iso(),
                "phone": phone,
                "name": name,
                "campaign_id": campaign_id,
                "env_name": env_name,
                "template": template_path,
                "template_weight": str(template_weight),
                "queue_status_before": queue_status_before,
                "result_status": result_status,
                "attempt_no": str(next_attempt_no),
                "status_code": str(status_code),
                "success": str(success),
            })

            processed_count += 1

            if did_message:
                sent_or_dryrun_count += 1
                processed_since_batch += 1

                if sent_or_dryrun_count < len(queue_items):
                    if processed_since_batch >= next_batch_after:
                        sleep_s = rng.randint(batch_min, batch_max)
                        print(
                            f"[PAUSE] batch pause {sleep_s}s "
                            f"after {processed_since_batch} msgs in current batch "
                            f"(total_processed={processed_count})"
                        )
                        time.sleep(sleep_s)
                        processed_since_batch = 0
                        next_batch_after = rng.randint(batch_size_min, batch_size_max)
                        print(f"[INFO] next_batch_after={next_batch_after} messages")
                    else:
                        sleep_s = rng.randint(per_min, per_max)
                        print(
                            f"[WAIT] per-message pause {sleep_s}s "
                            f"(msg_in_batch={processed_since_batch}/{next_batch_after})"
                        )
                        time.sleep(sleep_s)

        print(f"[DONE] processed={processed_count} log={log_csv} db={db_path}")
        print_queue_summary(conn, campaign_id, env_name)

        failed_export = export_failed_list(conn, campaign_id, env_name)
        if failed_export:
            print(f"[EXPORT] failed list: {failed_export}")

        summary_text = build_summary_text(
            conn=conn,
            campaign_id=campaign_id,
            env_name=env_name,
            run_id=run_id,
            processed_count=processed_count,
            failed_export_path=failed_export
        )
        send_telegram_report(summary_text)
        send_discord_report(summary_text)

    finally:
        release_file_lock(lock_fp)


if __name__ == "__main__":
    main()
