# Common SQL & MySQL Commands

> [← Back to Main Index](README.md)

## Table of Contents

- [Overview](#overview)
- [SQL / MySQL Administration Commands](#sql--mysql-administration-commands)
  - [Connection & Inspection](#connection--inspection)
  - [User & Password Management](#user--password-management)
- [Database Backups & Restoration](#database-backups--restoration)
  - [Exporting & Importing with `mysqldump`](#exporting--importing-with-mysqldump)
  - [Cold File-Level Backup (Root Access Only)](#cold-file-level-backup-root-access-only)
  - [Automated Daily MySQL Backup Script](#automated-daily-mysql-backup-script)

---

## Overview

A collection of frequently used SQL / MySQL administration commands and backup procedures.

> **Note:** Many time-series databases such as **InfluxDB** use an SQL-like query syntax (`SHOW DATABASES`, `USE`, `SELECT`, etc.) that closely mirrors standard SQL.
>
> *Additional SQL basics reference: [freeCodeCamp — Basic SQL Commands](https://www.freecodecamp.org/news/basic-sql-commands/)*

---

## SQL / MySQL Administration Commands

### Connection & Inspection

**Connect to a MySQL server:**

```bash
mysql -h localhost -u USER_NAME -p
# Password will be prompted
```

**Inspect server status, databases, tables, and fields:**

```sql
-- Show SQL server status
SHOW STATUS;

-- List all databases
SHOW DATABASES;

-- Select a database and list its tables
USE mysql;
SHOW TABLES;

-- Show fields/columns in a table
DESCRIBE TABLE_NAME;
-- e.g.: DESCRIBE user;
```

### User & Password Management

**List all MySQL users:**

```sql
SELECT user FROM mysql.user;
```

**Update a user's password:**

```sql
UPDATE user SET authentication_string = PASSWORD("NewPassword") WHERE User = 'UserName';

-- Or:
SET authentication_string FOR 'UserName'@'localhost' = PASSWORD('NewPassword');
```

**Create a user, grant privileges, and set query limits:**
*(Source: [MySQL 5.7 Reference Manual — GRANT](https://dev.mysql.com/doc/refman/5.7/en/grant.html))*

```sql
CREATE USER 'UserName'@'localhost' IDENTIFIED BY 'mypass';
GRANT ALL ON db1.* TO 'UserName'@'localhost';
GRANT SELECT ON db2.invoice TO 'UserName'@'localhost';
ALTER USER 'UserName'@'localhost' WITH MAX_QUERIES_PER_HOUR 90;
```

---

## Database Backups & Restoration

### Exporting & Importing with `mysqldump`

**Dump all databases for backup (export):**

```bash
mysqldump --all-databases > dump-$(date '+%Y-%m-%d_%H-%M-%S').sql -u root -p
```

**Import a SQL backup into a new database:**

```sql
CREATE DATABASE new_database;
```

```bash
mysql -u username -p new_database < data-dump.sql
```

**Verify an SQL dump file:**

```bash
head -n 5 data-dump.sql
tail -n 5 data-dump.sql
```

### Cold File-Level Backup (Root Access Only)

When you do not have MySQL credentials but have `root` access on the host:

```bash
/etc/init.d/mysql stop
mkdir -p /opt/database/backup-$(date -I)/
cp -R /var/lib/mysql/* /opt/database/backup-$(date -I)/
cd /opt/database/backup-$(date -I)
tar -czfv * > /opt/mysqlBackup-$(date -I).tar.gz
/etc/init.d/mysql start
```

### Automated Daily MySQL Backup Script

*Source: [Farzad Farid — `mysql-backup` Gist](https://gist.github.com/Farzy/662842)*

```bash
#!/bin/bash
# Daily MySQL backup tool
#
# Author: Farzad FARID ffarid@pragmatic-source.com
# Date: 04/11/2010
#####################################################################
# BASH SETTINGS
#####################################################################

# Stop script on any uncaught error
set -e
# Catch uninitialized variables
set -u

#####################################################################
# CONFIGURATION
#####################################################################

# Destination directory (e.g., NFS mount)
BACKUP_DIR=/srv/backup/mysql
# MySQL config file containing credentials with sufficient rights for mysqldump
MY_CONF=/root/.my.cnf
# Backup retention period (in days)
RETENTION=7
# Space-separated list of databases to exclude
DB_EXCLUDE="information_schema"
# Create a subdirectory per host (1 = yes, 0 = no)
FOLDER_PER_HOST=1
# Create a subdirectory per database (1 = yes, 0 = no)
FOLDER_PER_BASE=1
# mysqldump options
MY_OPTS="--opt --complete-insert --routines --single-transaction --max_allowed_packet=32M"

# Internal variables (usually do not need modification)
# -----------------------------------------------------
DATE=`date +%Y%m%d-%H%M`
PREFIX=${HOSTNAME%%.*}_mysql_backup

PROGNAME=mysql-backup
LOCKFILE=/var/tmp/${PROGNAME}.lock

MYSQL="/usr/bin/mysql"
MYSQLDUMP="/usr/bin/mysqldump"

# Syslog helper function
# Arguments:
#  - Syslog level (info, warning, error...)
#  - Message to log
function log() {
  loglevel=$1
  shift
  msg="$*"

  logger -p user.${loglevel} -t "${PROGNAME}[$$]" ${msg}
}

#################################
# Clean old backups
# Arguments:
# - Folder to clean
# - File prefix
# - Retention (days)
#################################
function clean_backups() {
  local dir=$1 prefix=$2 retention=$3

  # Set backup file's mtime according to the date in the filename
  find "${dir}" -name .snapshot -prune -o -type f -name "${prefix}*" -print0 | while read -d $'\0' file ; do
    # Extract file date as YYYYMMDDhhmm
    file_date=$(echo ${file} | sed -e 's/^.*\.\([0-9]\{8\}\)-\([0-9]\{4\}\).*$/\1\2/')
    touch -t ${file_date} ${file}
  done
  # Delete dumps older than the configured retention period
  find "${dir}" -type f -name "${prefix}*" -mtime +${retention} -exec rm -f "{}" \; 2>/dev/null
}

#####################################################################
# Main function
#####################################################################

function main() {
  log info "Début de la sauvegarde MySQL"

  # Query MySQL for all database names
  databases=`${MYSQL} --defaults-extra-file=${MY_CONF} -Bse "show databases"`
  if [ $? -ne 0 ]; then
    log error "ERREUR d'accès au serveur MySQL. La requête 'show databases' a échoué."
    exit 1
  fi

  # Exclude configured databases
  if [ -n "${DB_EXCLUDE}" ]; then
      reg=$(echo ${DB_EXCLUDE} | sed -e 's/ /\\\|/')
      reg="\(${reg}\)"
      databases=$(echo ${databases} | sed -e "s/${reg}//g")
  fi

  # Dump each database
  for base in ${databases}
  do
    DUMP_DIR=${BACKUP_DIR}
    if [ ${FOLDER_PER_HOST} -eq 1 ]; then
        DUMP_DIR=${DUMP_DIR}/${HOSTNAME%%.*}
    fi
    if [ ${FOLDER_PER_BASE} -eq 1 ]; then
        DUMP_DIR=${DUMP_DIR}/${base}
    fi
    mkdir -p ${DUMP_DIR}

    log info "Dump de la base ${base}..."
    ${MYSQLDUMP} --defaults-extra-file=${MY_CONF} ${MY_OPTS} ${base} \
      | bzip2 -9 > ${DUMP_DIR}/${PREFIX}_${base}.${DATE}.sql.bz2
    if [ $? -ne 0 ]; then
      log error "ERREUR lors du dump de la base ${base}."
    fi
  done

  # Clean old backups for this server
  clean_backups ${BACKUP_DIR} ${PREFIX} ${RETENTION}

  log info "Fin de la sauvegarde MySQL"
}

#####################################################################
# Entry point and lockfile management to prevent concurrent runs
#####################################################################
if ( set -o noclobber; echo "$$" > "$LOCKFILE") 2> /dev/null;
then
   trap 'rm -f "$LOCKFILE"; exit $?' INT TERM EXIT

   main

   rm -f "$LOCKFILE"
   trap - INT TERM EXIT
   exit 0
else
   (
     echo "Failed to acquire lockfile: $LOCKFILE."
     echo "Held by following process:"
     ps -p $(cat $LOCKFILE) uww
   ) | log error
   exit 1
fi
```
