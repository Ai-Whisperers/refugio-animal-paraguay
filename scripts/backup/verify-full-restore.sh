#!/usr/bin/env bash
# verify-full-restore.sh — Weekly restore test: restores latest backup to a temp database.
#
# Verifies that the backup is actually restorable, not just readable as gzip.
# The temp database is dropped after the test regardless of outcome.
#
# Usage:
#   /opt/backups/verify-full-restore.sh
#
# Crontab entry (run as root — weekly on Sunday at 04:00 UTC):
#   0 4 * * 0 /opt/backups/verify-full-restore.sh >> /var/log/backup.log 2>&1
#
# Requirements:
#   - docker must be accessible
#   - The postgres container must be running
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
DB_CONTAINER="${DB_CONTAINER:-refugio-db-1}"
DB_NAME="${DB_NAME:-refugio_prod}"
DB_USER="${DB_USER:-refugio_user}"
TEMP_DB="refugio_verify_$$"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "Starting weekly full-restore verification test"

# Find latest backup.
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}/${DB_NAME}_"*.sql.gz 2>/dev/null | head -1 || true)
if [[ -z "${LATEST_BACKUP}" ]] || [[ ! -f "${LATEST_BACKUP}" ]]; then
    log "ERROR: No backup file found in ${BACKUP_DIR}"
    logger -t refugio-backup "Full restore test FAILED: no backup file found"
    exit 1
fi

log "Using backup: ${LATEST_BACKUP}"

# Cleanup function — always drop the temp database.
cleanup() {
    log "Dropping temp database ${TEMP_DB}"
    docker exec "${DB_CONTAINER}" \
        psql --username="${DB_USER}" --no-password postgres \
        --command="DROP DATABASE IF EXISTS ${TEMP_DB};" 2>/dev/null || true
}
trap cleanup EXIT

# Create temp database inside the container.
log "Creating temp database: ${TEMP_DB}"
docker exec "${DB_CONTAINER}" \
    psql --username="${DB_USER}" --no-password postgres \
    --command="CREATE DATABASE ${TEMP_DB};"

# Restore backup into temp database.
log "Restoring backup into ${TEMP_DB}..."
if gunzip -c "${LATEST_BACKUP}" \
    | docker exec --interactive "${DB_CONTAINER}" \
        psql --username="${DB_USER}" --no-password "${TEMP_DB}" \
        --quiet 2>&1; then
    log "Restore succeeded."
else
    log "ERROR: Restore failed."
    logger -t refugio-backup "Full restore test FAILED: psql restore error — ${LATEST_BACKUP}"
    exit 1
fi

# Count tables in restored database.
RESTORED_TABLES=$(docker exec "${DB_CONTAINER}" \
    psql --username="${DB_USER}" --no-password "${TEMP_DB}" \
    --tuples-only --command="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" \
    | tr -d '[:space:]')

log "Restored table count: ${RESTORED_TABLES}"

if (( RESTORED_TABLES < 5 )); then
    log "WARNING: Restored database has fewer than 5 tables — may indicate incomplete restore."
    logger -t refugio-backup "Full restore test WARNING: only ${RESTORED_TABLES} tables restored from ${LATEST_BACKUP}"
    exit 1
fi

log "Full restore test PASSED. ${RESTORED_TABLES} tables restored from ${LATEST_BACKUP}"
logger -t refugio-backup "Full restore test PASSED: ${RESTORED_TABLES} tables — ${LATEST_BACKUP}"
