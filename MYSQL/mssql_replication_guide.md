
# MSSQL Transactional Replication Setup Guide

This guide provides a step-by-step process to set up MSSQL Transactional Replication between two servers.

## Server Details
- **Source:** MSSQL 2018 on `103.104.138.XXX` (Database: `OrionProd`)
- **Destination:** MSSQL 2020 on `103.104.136.XXX` (Database: `OrionProd`)
- **Login Credentials:** `swSOLuser / PASWDKETIKDISINI`

---

## Step 1: Verify SQL Server Agent is Running on Both Servers
1. Open **SQL Server Configuration Manager** on both servers.
2. Ensure **SQL Server Agent** is running.
3. If not running, start the service and set it to **Automatic** startup.

---

## Step 2: Configure the Distributor (on Source Server 103.104.138.xxx)

```sql
USE master
GO
-- Configure the distributor
EXEC sp_adddistributor 
    @distributor = @@SERVERNAME,
    @password = 'PASWDKETIKDISINI'
GO

-- Create the distribution database
EXEC sp_adddistributiondb 
    @database = 'distribution',
    @data_folder = N'C:\Program Files\Microsoft SQL Server\MSSQL18.MSSQLSERVER\MSSQL\DATA',
    @log_folder = N'C:\Program Files\Microsoft SQL Server\MSSQL18.MSSQLSERVER\MSSQL\DATA'
GO

-- Add the publisher
EXEC sp_adddistpublisher 
    @publisher = @@SERVERNAME,
    @distribution_db = 'distribution',
    @security_mode = 0,
    @login = 'swSOLuser',
    @password = 'PASWDKETIKDISINI'
GO
```

---

## Step 3: Enable the Database for Replication

```sql
USE master
GO
EXEC sp_replicationdboption 
    @dbname = N'OrionProd', 
    @optname = N'publish', 
    @value = N'true'
GO

-- Verify that publishing is enabled:
SELECT is_published FROM sys.databases WHERE name = 'OrionProd'
GO
```

---

## Step 4: Create the Publication

```sql
USE OrionProd
GO
EXEC sp_addpublication 
    @publication = N'OrionProd_Pub',
    @description = N'Publication for OrionProd database',
    @sync_method = N'concurrent',
    @retention = 0,
    @allow_push = N'true',
    @allow_pull = N'true',
    @allow_anonymous = N'false',
    @enabled_for_internet = N'false',
    @snapshot_in_defaultfolder = N'true'
GO

-- Add the Snapshot Agent
EXEC sp_addpublication_snapshot 
    @publication = N'OrionProd_Pub',
    @frequency_type = 1,
    @frequency_interval = 1
GO
```

---

## Step 5: Add All Tables to the Publication

```sql
DECLARE @publication NVARCHAR(100) = 'OrionProd_Pub'
DECLARE @tableName NVARCHAR(100)

DECLARE table_cursor CURSOR FOR
SELECT name FROM sys.tables

OPEN table_cursor
FETCH NEXT FROM table_cursor INTO @tableName

WHILE @@FETCH_STATUS = 0
BEGIN
    EXEC sp_addarticle 
        @publication = @publication,
        @article = @tableName,
        @source_owner = 'dbo',
        @source_object = @tableName,
        @type = 'logbased',
        @description = 'Replication for ' + @tableName
    FETCH NEXT FROM table_cursor INTO @tableName
END

CLOSE table_cursor
DEALLOCATE table_cursor
```

---

## Step 6: Add the Subscription (on Source Server)

```sql
USE SolarWindsOrionProd
GO
EXEC sp_addsubscription 
    @publication = N'OrionProd_Pub',
    @subscriber = '103.104.136.XXX',
    @destination_db = N'OrionProd',
    @subscription_type = N'Push',
    @sync_type = N'automatic',
    @article = N'all',
    @update_mode = N'read only'
GO

EXEC sp_addpushsubscription_agent 
    @publication = N'OrionProd_Pub',
    @subscriber = '103.104.136.XXX',
    @subscriber_db = N'OrionProd',
    @subscriber_security_mode = 0,
    @subscriber_login = 'swSOLuser',
    @subscriber_password = 'PASWDKETIKDISINI',
    @frequency_type = 64,
    @frequency_interval = 1
GO
```

---

## Step 7: Prepare the Destination Server (103.104.136.XXX)

```sql
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'OrionProd')
BEGIN
    CREATE DATABASE OrionProd
END
GO
```

Ensure SQL Server Agent is running on the destination server.

---

## Step 8: Monitor Replication

```sql
USE OrionProd
GO
EXEC sp_helppublication
GO

EXEC sp_helpsubscription 
    @publication = 'OrionProd_Pub'
GO

-- Monitor transaction counts:
EXEC sp_replcounters;
```

---

## Step 9: Continuous Replication Setup
- SQL Server Agent handles continuous replication.
- Ensure the **Snapshot Agent**, **Log Reader Agent**, and **Distribution Agent** jobs are running.

---

## Key Differences from MySQL Master-Slave Setup
- MSSQL uses **Transactional Replication** instead of binary logs.
- No `CHANGE MASTER TO` command; instead, configure **Publisher**, **Distributor**, and **Subscriber** roles.
- Replication managed by **SQL Server Agent Jobs**.
