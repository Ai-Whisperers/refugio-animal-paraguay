#!/usr/bin/env bash
# cleanup.sh — Remove backups older than RETENTION_DAYS.
#
# Keeps a minimum of MIN_KEEP recent backups regardless of age,
# so retention never leaves us with zero backups.
#
# Usage:
#   /opt/backups/cleanup.sh
#
# Crontab entry (run as root — daily at 03:00 UTC, after backup.sh):
#   0 3 * * * /opt/backups/cleanup.sh >> /var/log/backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
DB_NAME="${DB_NAME:-refugio_prod}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
MIN_KEEP="${MIN_KEEP:-5}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "Running backup cleanup (retention: ${RETENTION_DAYS} days, min keep: ${MIN_KEEP})"

# Collect all backup files sorted newest-first.
mapfile -t ALL_BACKUPS < <(ls -t "${BACKUP_DIR}/${DB_NAME}_"*.sql.gz 2>/dev/null || true)
TOTAL=${#ALL_BACKUPS[@]}

if (( TOTAL == 0 )); then
    log "No backup files found in ${BACKUP_DIR}."
    exit 0
fi

log "Found ${TOTAL} backup file(s)."

DELETED=0
for ((i = 0; i < TOTAL; i++)); do
    BACKUP="${ALL_BACKUPS[$i]}"

    # Always keep the MIN_KEEP most recent backups.
    if (( i < MIN_KEEP )); then
        continue
    fi

    # Delete if older than RETENTION_DAYS.
    if find "${BACKUP}" -mtime "+${RETENTION_DAYS}" | grep -q .; then
        log "Deleting: ${BACKUP}"
        rm -f "${BACKUP}"
        (( DELETED++ )) || true
    fi
done

log "Cleanup complete. Deleted ${DELETED} backup(s)."
logger -t refugio-backup "Backup cleanup: removed ${DELETED} file(s) older than ${RETENTION_DAYS} days"
