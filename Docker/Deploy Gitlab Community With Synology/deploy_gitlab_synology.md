# 🚀 Deploying GitLab CE on Synology NAS with Docker Compose

This tutorial walks through deploying GitLab Community Edition on a Synology NAS using Docker Compose. It includes DDNS configuration, SSL certificate integration with Let's Encrypt, and periodic certificate renewal automation.

---

## 📦 Requirements

- Synology NAS with Docker package installed
- Synology DDNS domain (e.g., `your-domain.synology.me`)
- Admin SSH access to the NAS
- Docker Compose available on the system (manual install might be needed)
- DSM configured to issue Let's Encrypt SSL certificates

---

## 🛠 Step 1: Prepare Your Folders

Open SSH to your Synology NAS and run:

```bash
mkdir -p /volume1/docker/gitlab-server
cd /volume1/docker/gitlab-server
```

This will be the root folder for your GitLab Docker Compose setup.

---

## 🔧 Step 2: Create `docker-compose.yaml`

Create a file named `docker-compose.yaml` inside the folder:

```yaml
version: '3.6'
services:
  gitlab:
    image: gitlab/gitlab-ce:17.8.1-ce.0
    container_name: gitlab
    restart: always
    ports:
      - '6022:22'
      - '6443:6443'
    shm_size: 256m
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        letsencrypt['enable'] = false
        gitlab_shell_ssh_port = 6022
        external_url 'https://your-domain.synology.me:6443'
        gitlab_rails['time_zone'] = 'Asia/Taipei'
        gitlab_rails['lfs_enabled'] = true
        nginx['redirect_http_to_https'] = true
        gitlab_rails['gitlab_username_changing_enabled'] = false
    volumes:
      - './gitlab/config:/etc/gitlab:z'
      - './gitlab/config/ssl:/etc/gitlab/ssl:z'
      - './gitlab/logs:/var/log/gitlab:z'
      - './gitlab/data:/var/opt/gitlab:z'
```

Change `your-domain.synology.me` to your Synology DDNS domain.

---

## 📜 Step 3: SSL Setup and Certificate Copy

Synology stores Let's Encrypt certificates in:

```
/usr/syno/etc/certificate/_archive/${DEFAULT}
```

Create a script named `cron.sh`:

```bash
#!/bin/bash
domain=$1
ssl_dir="/volume1/docker/gitlab-server/gitlab/config/ssl"
cert_dir="/usr/syno/etc/certificate/_archive/$(cat /usr/syno/etc/certificate/_archive/DEFAULT)"

mkdir -p "$ssl_dir"

cp "$cert_dir/fullchain.pem" "$ssl_dir/$domain.crt"
cp "$cert_dir/privkey.pem" "$ssl_dir/$domain.key"

docker exec gitlab gitlab-ctl hup nginx
docker exec gitlab gitlab-ctl hup registry
```

This script updates the SSL files and reloads NGINX inside the GitLab container.

---

## 🧪 Step 4: Launch GitLab with Setup Script

Create `setup.sh`:

```bash
#!/bin/bash
domain=$1

mkdir -p gitlab/config/ssl gitlab/logs gitlab/data
chmod -R 777 gitlab

./cron.sh $domain

docker-compose up -d
```

Start GitLab:

```bash
chmod +x setup.sh cron.sh
sudo ./setup.sh your-domain.synology.me
```

---

## 🧰 Step 5: Access GitLab

- Web: `https://your-domain.synology.me:6443`
- SSH: `ssh -p 6022 git@your-domain.synology.me`

Retrieve initial password:

```bash
cat gitlab/config/initial_root_password
```

---

## 🔐 Step 6: Security & Firewall

Use Synology DSM to:
- Restrict access to port 6443 to trusted IPs only
- Enable auto-renewal of Let's Encrypt and trigger `cron.sh` via Task Scheduler monthly

---

## 💾 Step 7: Backup

Use Synology **Hyper Backup** to regularly back up:
```
/volume1/docker/gitlab-server
```

---

## 👥 Step 8: Add Users via Console

```bash
docker exec -it gitlab gitlab-rails console
```

Add users via Ruby script:

```ruby
user = User.new(username: 'john', name: 'John Doe', email: 'john@example.com', password: 'StrongPassword123', skip_confirmation: true)
user.save!
```

---

## ✅ Conclusion

You’ve successfully deployed GitLab CE on Synology NAS using Docker Compose and integrated it with Synology's built-in DDNS + SSL! Ideal for private repositories and internal CI/CD.