# MySQL/MariaDB Database Replication Setup Guide

## Overview
This guide explains how to set up master-slave replication in MySQL/MariaDB for databases db_A, db_B, and db_C. The setup involves creating a backup of the master database and configuring a slave server to replicate from the master.

## Prerequisites
- Two MySQL/MariaDB servers:
  - Master server (IP: 192.168.1.10, Port: 3306)
  - Slave server (IP: 192.168.1.17, Port: 3306)
- User accounts with appropriate privileges
- Network connectivity between servers

## Step 1: Create Database Backup
On the master server, create a backup of the specified databases:

```bash
nohup mysql-dump -u userdbnya -ppassworduserdb -h 192.168.1.10 -P 3306 \
--databases db_A db_B db_C \
--single-transaction \
--skip-lock-tables \
--skip-triggers \
--master-data=2 > bebasnamaoutputbakupnya.sql &
```

### Command explanation:
- `nohup`: Runs the command in the background, continues even if the terminal closes
- `--single-transaction`: Creates a consistent backup without locking tables
- `--skip-lock-tables`: Prevents table locking during backup
- `--skip-triggers`: Excludes triggers from the backup
- `--master-data=2`: Includes master binary log position as a commented CHANGE MASTER command

## Step 2: Import Backup to Slave
Transfer and import the backup file to the slave server:

```bash
nohup mysql -u userdbnya -ppassworduserdb -h 192.168.1.17 -P 3306 < bebasnamaoutputbakupnya.sql &
```

## Step 3: Configure Slave Replication
On the slave server, configure replication settings:

```sql
CHANGE MASTER 'server_slave' TO
MASTER_HOST="192.168.1.10",
MASTER_PORT=3306,
MASTER_USER="userdbnya",
MASTER_PASSWORD="passworduserdb",
MASTER_LOG_FILE='mariadb-bin.692683',
MASTER_LOG_POS=23651185,
MASTER_USE_GTID=no;
```

### Parameter explanation:
- `MASTER_HOST`: IP address of the master server
- `MASTER_PORT`: MySQL/MariaDB port on master server
- `MASTER_USER`: Replication user account
- `MASTER_LOG_FILE`: Binary log file name from master
- `MASTER_LOG_POS`: Position in binary log to start replication
- `MASTER_USE_GTID`: Disable GTID-based replication

## Step 4: Start Slave Replication
Execute these commands on the slave server:

```sql
STOP SLAVE 'server_slave';
START SLAVE 'server_slave';
```

## Step 5: Configure Replication Filters
Edit the MySQL configuration file on the slave server:

```bash
vim /etc/mysql/my.cnf
```

Add these lines to specify which databases to replicate:

```ini
server_slave.replicate-do-db = db_A
server_slave.replicate-do-db = db_B
server_slave.replicate-do-db = db_C
```

## Verification
To verify replication status:

```sql
SHOW SLAVE 'server_slave' STATUS\G
```

## Important Notes
1. Always verify binary log settings on the master server
2. Monitor replication lag regularly
3. Ensure sufficient disk space on both servers
4. Keep backup files until replication is confirmed working
5. Consider implementing backup rotation strategy

## Troubleshooting
- Check network connectivity between servers
- Verify user privileges
- Monitor error logs for replication issues
- Ensure binary logging is enabled on master
- Verify slave has sufficient resources to keep up with master
