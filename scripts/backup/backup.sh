#!/usr/bin/env bash
# backup.sh — Create a compressed PostgreSQL dump of the production database.
#
# Usage (run as root or a user with docker access):
#   /opt/backups/backup.sh
#
# Environment variables (all optional, defaults match production docker-compose):
#   BACKUP_DIR     Directory to store backups  (default: /opt/backups)
#   COMPOSE_DIR    Directory of docker-compose.prod.yml  (default: /opt/refugio)
#   DB_CONTAINER   Name of the postgres container  (default: refugio-db-1)
#   DB_NAME        Database name  (default: refugio_prod)
#   DB_USER        PostgreSQL user  (default: refugio_user)
#
# Crontab entry (run as root — daily at 02:00 UTC):
#   0 2 * * * /opt/backups/backup.sh >> /var/log/backup.log 2>&1
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
DB_CONTAINER="${DB_CONTAINER:-refugio-db-1}"
DB_NAME="${DB_NAME:-refugio_prod}"
DB_USER="${DB_USER:-refugio_user}"
TIMESTAMP=$(date -u +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "Starting backup of ${DB_NAME} from container ${DB_CONTAINER}"

# Ensure backup directory exists and is restricted.
if [[ ! -d "${BACKUP_DIR}" ]]; then
    log "ERROR: Backup directory ${BACKUP_DIR} does not exist. Run setup.sh first."
    exit 1
fi

# Dump database via docker exec, pipe through gzip.
# We use --no-password here because credentials come from the container environment.
if docker exec "${DB_CONTAINER}" pg_dump \
        --username="${DB_USER}" \
        --no-password \
        --format=plain \
        "${DB_NAME}" \
    | gzip --best > "${BACKUP_FILE}"; then
    log "Dump written: ${BACKUP_FILE}"
else
    log "ERROR: pg_dump failed. Removing partial file."
    rm -f "${BACKUP_FILE}"
    logger -t refugio-backup "Database backup FAILED: pg_dump error — check /var/log/backup.log"
    exit 1
fi

# Verify gzip integrity.
if gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    BACKUP_SIZE=$(stat --format="%s" "${BACKUP_FILE}")
    log "Backup verified. File size: ${BACKUP_SIZE} bytes."
    logger -t refugio-backup "Database backup succeeded: ${BACKUP_FILE} (${BACKUP_SIZE} bytes)"
else
    log "ERROR: Backup file failed integrity check — removing corrupted file."
    rm -f "${BACKUP_FILE}"
    logger -t refugio-backup "Database backup FAILED: integrity check — ${BACKUP_FILE}"
    exit 1
fi

# Warn if the backup is suspiciously small (< 100 KB likely indicates an empty dump).
MIN_BYTES=102400
if (( BACKUP_SIZE < MIN_BYTES )); then
    log "WARNING: Backup is unusually small (${BACKUP_SIZE} bytes < ${MIN_BYTES} threshold). Inspect manually."
    logger -t refugio-backup "Database backup WARNING: small file — ${BACKUP_FILE} (${BACKUP_SIZE} bytes)"
fi

log "Backup complete: ${BACKUP_FILE}"
