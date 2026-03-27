#!/usr/bin/env bash
# setup.sh — One-time setup: create backup directory and install cron jobs.
#
# Run as root on the production VPS once, before the first backup.
#
# Usage:
#   sudo /opt/refugio/scripts/backup/setup.sh
set -euo pipefail

BACKUP_DIR="/opt/backups"
SCRIPTS_DIR="/opt/backups"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "Setting up Refugio Animal Paraguay backup system"

# 1. Create backup directory.
if [[ ! -d "${BACKUP_DIR}" ]]; then
    log "Creating backup directory: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"
fi
chmod 700 "${BACKUP_DIR}"
log "Backup directory ready: ${BACKUP_DIR} (permissions: 700)"

# 2. Copy scripts to /opt/backups/.
log "Installing backup scripts to ${SCRIPTS_DIR}"
for SCRIPT in backup.sh cleanup.sh verify.sh verify-full-restore.sh; do
    cp "${SOURCE_DIR}/${SCRIPT}" "${SCRIPTS_DIR}/${SCRIPT}"
    chmod 750 "${SCRIPTS_DIR}/${SCRIPT}"
    log "  Installed: ${SCRIPTS_DIR}/${SCRIPT}"
done

# 3. Copy restore instructions.
cp "${SOURCE_DIR}/RESTORE_INSTRUCTIONS.md" "${BACKUP_DIR}/RESTORE_INSTRUCTIONS.md"
chmod 640 "${BACKUP_DIR}/RESTORE_INSTRUCTIONS.md"
log "  Installed: ${BACKUP_DIR}/RESTORE_INSTRUCTIONS.md"

# 4. Install cron jobs (replace existing refugio-backup entries).
CRONTAB_TEMP=$(mktemp)
crontab -l 2>/dev/null | grep -v "refugio-backup\|/opt/backups/" > "${CRONTAB_TEMP}" || true

cat >> "${CRONTAB_TEMP}" << 'CRON'
# Refugio Animal Paraguay — Database Backup
# Daily backup at 02:00 UTC
0 2 * * * /opt/backups/backup.sh >> /var/log/backup.log 2>&1
# Daily cleanup at 03:00 UTC (after backup)
0 3 * * * /opt/backups/cleanup.sh >> /var/log/backup.log 2>&1
# Weekly full restore test on Sunday at 04:00 UTC
0 4 * * 0 /opt/backups/verify-full-restore.sh >> /var/log/backup.log 2>&1
CRON

crontab "${CRONTAB_TEMP}"
rm -f "${CRONTAB_TEMP}"

log "Cron jobs installed:"
crontab -l | grep -A1 "Refugio"

# 5. Create log file.
touch /var/log/backup.log
chmod 640 /var/log/backup.log
log "Log file ready: /var/log/backup.log"

# 6. Run a quick sanity test.
log "Running initial backup verification (dry-run connectivity check)..."
if docker ps --format '{{.Names}}' | grep -q "db"; then
    log "  Docker postgres container found."
else
    log "  WARNING: No postgres container found. Ensure Docker Compose is running before first backup."
fi

log ""
log "Setup complete. Run a manual test backup with:"
log "  sudo /opt/backups/backup.sh"
log ""
log "Monitor backups with:"
log "  tail -f /var/log/backup.log"
