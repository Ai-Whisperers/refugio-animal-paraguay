#!/usr/bin/env bash
# verify.sh — Check integrity of the most recent backup.
#
# Verifies gzip integrity and size of the latest backup file.
# Run manually or add to crontab for daily checks.
#
# Usage:
#   /opt/backups/verify.sh
#   /opt/backups/verify.sh /opt/backups/specific_file.sql.gz
#
# Exit codes:
#   0 — backup verified successfully
#   1 — no backups found
#   2 — integrity check failed
#   3 — backup is suspiciously small
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
DB_NAME="${DB_NAME:-refugio_prod}"
MIN_BYTES="${MIN_BYTES:-102400}"  # 100 KB

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

# Use provided file or find the latest.
if [[ -n "${1:-}" ]]; then
    BACKUP_FILE="$1"
else
    BACKUP_FILE=$(ls -t "${BACKUP_DIR}/${DB_NAME}_"*.sql.gz 2>/dev/null | head -1 || true)
fi

if [[ -z "${BACKUP_FILE}" ]] || [[ ! -f "${BACKUP_FILE}" ]]; then
    log "ERROR: No backup file found in ${BACKUP_DIR}"
    logger -t refugio-backup "Backup verification FAILED: no backup file found"
    exit 1
fi

log "Verifying backup: ${BACKUP_FILE}"

# Test gzip integrity.
if ! gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    log "ERROR: Backup file is corrupted: ${BACKUP_FILE}"
    logger -t refugio-backup "Backup verification FAILED: corrupted — ${BACKUP_FILE}"
    exit 2
fi

BACKUP_SIZE=$(stat --format="%s" "${BACKUP_FILE}")
log "Backup size: ${BACKUP_SIZE} bytes"

# Warn if suspiciously small (may indicate empty dump).
if (( BACKUP_SIZE < MIN_BYTES )); then
    log "ERROR: Backup is suspiciously small (${BACKUP_SIZE} bytes < ${MIN_BYTES} minimum)."
    logger -t refugio-backup "Backup verification FAILED: small file (${BACKUP_SIZE} bytes) — ${BACKUP_FILE}"
    exit 3
fi

# Check that the file contains SQL CREATE statements (basic content check).
if ! gunzip -c "${BACKUP_FILE}" 2>/dev/null | head -200 | grep -qi "CREATE TABLE\|PostgreSQL database dump"; then
    log "WARNING: Backup file does not appear to contain expected SQL — inspect manually."
    logger -t refugio-backup "Backup verification WARNING: unexpected content — ${BACKUP_FILE}"
fi

log "Backup verification PASSED: ${BACKUP_FILE} (${BACKUP_SIZE} bytes)"
logger -t refugio-backup "Backup verification passed: ${BACKUP_FILE} (${BACKUP_SIZE} bytes)"
