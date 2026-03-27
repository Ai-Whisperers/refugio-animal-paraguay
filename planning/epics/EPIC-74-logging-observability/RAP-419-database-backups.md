---
story: RAP-419
epic: EPIC-74
title: "Set up automated database backups"
status: ready
priority: 1
points: 5
created: 2026-03-27
---

# RAP-419: Set Up Automated Database Backups

## Story

As an **operations engineer**, I want **daily automated database backups with 30-day retention** so that **data loss can be recovered**.

## Description

Production database (`refugio_prod` on VPS) needs automated daily backups using `pg_dump`, compression, and 30-day retention. Backups should be verified and stored securely on the VPS.

## Acceptance Criteria

### Backup Directory Setup

**Given** VPS with production PostgreSQL
**When** backup system is set up
**Then**
- [ ] Backup directory exists: `/opt/backups/`
- [ ] Directory is owned by postgres user or backup user
- [ ] Permissions are restrictive: `700` (only owner can read)
- [ ] Directory is on volume with enough space (at least 50GB free)

**Commands**:
```bash
sudo mkdir -p /opt/backups
sudo chown postgres:postgres /opt/backups
sudo chmod 700 /opt/backups
```

### Daily Backup Job

**Given** VPS runs backup job daily
**When** scheduled time arrives (e.g., 2 AM UTC)
**Then**
- [ ] `pg_dump` is executed for `refugio_prod` database
- [ ] Dump is compressed with gzip (reduces size ~10x)
- [ ] File is named with timestamp: `refugio_prod_YYYY-MM-DD_HH-MM-SS.sql.gz`
- [ ] File is stored in `/opt/backups/`

**Backup script: `/opt/backups/backup.sh`**:
```bash
#!/bin/bash

BACKUP_DIR="/opt/backups"
DB_NAME="refugio_prod"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Create backup
pg_dump $DB_NAME | gzip > "$BACKUP_FILE"

# Verify backup
if gzip -t "$BACKUP_FILE"; then
    echo "Backup successful: $BACKUP_FILE"
    # Log success
    logger -t backup "Database backup succeeded: $BACKUP_FILE"
else
    echo "Backup failed: $BACKUP_FILE"
    logger -t backup "Database backup FAILED: $BACKUP_FILE"
    exit 1
fi
```

### Cron Job Setup

**Given** backup script is ready
**When** cron job is configured
**Then**
- [ ] Cron job runs daily at 2 AM UTC: `0 2 * * *`
- [ ] Job runs backup script with proper permissions
- [ ] Output is logged to syslog

**Crontab entry** (run `sudo crontab -e` as root or postgres user):
```
# Run database backup daily at 2 AM UTC
0 2 * * * /opt/backups/backup.sh >> /var/log/backup.log 2>&1
```

### 30-Day Retention Policy

**Given** backups accumulate
**When** retention policy runs
**Then**
- [ ] Backups older than 30 days are deleted
- [ ] At least 30 latest backups are kept (even if > 30 days old)
- [ ] Deletion is logged

**Cleanup script: `/opt/backups/cleanup.sh`**:
```bash
#!/bin/bash

BACKUP_DIR="/opt/backups"
RETENTION_DAYS=30

# Delete backups older than 30 days
find $BACKUP_DIR -name "refugio_prod_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log cleanup
logger -t backup "Removed backups older than $RETENTION_DAYS days"
```

**Add to crontab** (run at 3 AM, after backup):
```
# Clean up old backups daily at 3 AM UTC
0 3 * * * /opt/backups/cleanup.sh
```

### Backup Verification

**Given** backup is created
**When** backup integrity check runs
**Then**
- [ ] Backup file is verified with `gzip -t`
- [ ] Backup file size is logged (to detect corrupted 0-byte files)
- [ ] Backup is tested by restoring to temp database (weekly)

**Verification script**: `/opt/backups/verify.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/opt/backups"
LATEST_BACKUP=$(ls -t $BACKUP_DIR/refugio_prod_*.sql.gz | head -1)

# Test gzip integrity
if ! gzip -t "$LATEST_BACKUP"; then
    logger -t backup "Backup verification FAILED: $LATEST_BACKUP is corrupted"
    exit 1
fi

# Check file size (should be > 100KB for our database)
SIZE=$(stat --format="%s" "$LATEST_BACKUP")
if [ $SIZE -lt 102400 ]; then
    logger -t backup "Backup verification WARNING: $LATEST_BACKUP is suspiciously small ($SIZE bytes)"
    exit 1
fi

logger -t backup "Backup verification passed: $LATEST_BACKUP ($SIZE bytes)"
```

**Weekly full restore test**:
```bash
#!/bin/bash

LATEST_BACKUP=$(ls -t /opt/backups/refugio_prod_*.sql.gz | head -1)
TEMP_DB="refugio_verify_$$"

# Create temp database
createdb $TEMP_DB

# Restore backup to temp database
gunzip -c "$LATEST_BACKUP" | psql $TEMP_DB

# Check if restore succeeded
if [ $? -eq 0 ]; then
    # Count tables (should match production)
    PROD_TABLES=$(psql -l | grep refugio_prod | wc -l)
    TEMP_TABLES=$(psql -l | grep $TEMP_DB | wc -l)
    if [ "$PROD_TABLES" -eq "$TEMP_TABLES" ]; then
        logger -t backup "Full restore test PASSED"
    else
        logger -t backup "Full restore test FAILED: Table count mismatch"
    fi
else
    logger -t backup "Full restore test FAILED: Restore error"
fi

# Drop temp database
dropdb $TEMP_DB
```

**Add to crontab** (weekly, e.g., Sunday at 4 AM):
```
# Test backup restoration weekly
0 4 * * 0 /opt/backups/verify-full-restore.sh
```

### Backup Monitoring

**Given** backups run daily
**When** backup job completes
**Then**
- [ ] Success/failure is logged
- [ ] Logs are queryable: `/var/log/backup.log`
- [ ] Failures trigger alerts (if monitoring in place)

**Monitoring checklist**:
- [ ] Last backup was created today
- [ ] Backup file size is reasonable (>100KB)
- [ ] Backup integrity passed gzip test
- [ ] No errors in `/var/log/backup.log`

### Backup Restore Procedure (Documentation)

Create: `/opt/backups/RESTORE_INSTRUCTIONS.md`

**To restore database from backup**:

```bash
# 1. Download backup file from /opt/backups/
# 2. Stop application
sudo systemctl stop refugio

# 3. Create new database (or drop existing to restore in-place)
dropdb refugio_prod  # or keep and restore to temp DB first
createdb refugio_prod

# 4. Restore from backup
gunzip -c refugio_prod_2026-03-27_02-00-00.sql.gz | psql refugio_prod

# 5. Verify restoration
psql refugio_prod -c "SELECT COUNT(*) FROM animals;"  # Should show animal count

# 6. Restart application
sudo systemctl start refugio
```

### Environment & Permissions

**Given** backup runs as postgres user
**When** backup script executes
**Then**
- [ ] Script has execute permissions: `chmod +x /opt/backups/backup.sh`
- [ ] postgres user has read/write to `/opt/backups/`
- [ ] postgres user can execute `pg_dump`

**Setup**:
```bash
sudo chmod +x /opt/backups/backup.sh
sudo chmod +x /opt/backups/cleanup.sh
sudo chmod +x /opt/backups/verify.sh
```

### Backup Encryption (Optional)

**Given** sensitive database with PII
**When** backups are stored
**Then** (optional): Backups can be encrypted with GPG

**Encrypted backup example**:
```bash
pg_dump $DB_NAME | gzip | gpg --encrypt --recipient backup@example.com > backup.sql.gz.gpg
```

## Definition of Done

- [ ] Backup directory created: `/opt/backups/`
- [ ] Backup script created and tested
- [ ] Cron job runs daily at 2 AM UTC
- [ ] Cleanup script removes backups > 30 days old
- [ ] Verification script tests backup integrity
- [ ] Weekly full restore test runs
- [ ] Last 30 backups are kept
- [ ] Backup logs are readable: `/var/log/backup.log`
- [ ] Restore instructions documented
- [ ] Code review (script review) approved
- [ ] Team is trained on restore procedure

## Technical Notes

### PostgreSQL Environment Variables

Scripts may need to set PostgreSQL connection info:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=password  # Or use .pgpass file
```

Or use `.pgpass` file (secure, no password in scripts):
```
# ~/.pgpass (permissions: 600)
localhost:5432:refugio_prod:postgres:password
```

### Backup Validation Checklist

- [ ] Backup file exists and has size > 100KB
- [ ] Backup file is readable: `gzip -t file.sql.gz`
- [ ] Backup is from correct database: `gunzip -c file.sql.gz | head -20 | grep "CREATE"`
- [ ] Last backup is recent (< 24 hours old)

### Monitoring Integration (optional)

If monitoring is in place, add checks:
- Alert if last backup is > 24 hours old
- Alert if backup file size is < 100KB (likely corrupted)
- Alert if gzip integrity check fails

---

*Last updated: 2026-03-27*
