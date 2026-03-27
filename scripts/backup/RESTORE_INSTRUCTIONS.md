# Database Restore Instructions

**IMPORTANT**: Read completely before restoring. Test the procedure first on a non-production database.

---

## When to Restore

- Data corruption detected
- Accidental deletion of records
- Disaster recovery (server failure)
- Production data needed for debugging

---

## 1. Locate the Backup

```bash
ls -lh /opt/backups/refugio_prod_*.sql.gz
```

Pick the appropriate backup. For recent data loss, use the most recent backup before the incident.

---

## 2. Verify Backup Integrity Before Restoring

```bash
/opt/backups/verify.sh /opt/backups/refugio_prod_YYYY-MM-DD_HH-MM-SS.sql.gz
```

If verification fails, try an older backup.

---

## 3. Partial Restore (Recovery without downtime)

Restore to a temporary database to retrieve specific records:

```bash
# Define the backup to restore
BACKUP="/opt/backups/refugio_prod_YYYY-MM-DD_HH-MM-SS.sql.gz"
CONTAINER="${DB_CONTAINER:-refugio-db-1}"
DB_USER="${DB_USER:-refugio_user}"
TEMP_DB="refugio_recovery_$(date +%s)"

# Create temp database
docker exec "${CONTAINER}" psql --username="${DB_USER}" postgres \
    --command="CREATE DATABASE ${TEMP_DB};"

# Restore backup
gunzip -c "${BACKUP}" | docker exec --interactive "${CONTAINER}" \
    psql --username="${DB_USER}" "${TEMP_DB}"

# Query the data you need
docker exec "${CONTAINER}" psql --username="${DB_USER}" "${TEMP_DB}" \
    --command="SELECT * FROM animals WHERE id = 42;"

# Clean up when done
docker exec "${CONTAINER}" psql --username="${DB_USER}" postgres \
    --command="DROP DATABASE ${TEMP_DB};"
```

---

## 4. Full Restore (Production downtime required)

**This replaces the entire production database. All changes since the backup will be lost.**

```bash
# 1. Stop the application (prevents new writes during restore)
cd /opt/refugio
docker compose -f docker-compose.prod.yml stop api

# 2. Connect to verify database state before dropping
docker exec refugio-db-1 psql --username=refugio_user refugio_prod \
    --command="SELECT COUNT(*) FROM animals;"

# 3. Drop and recreate the database
docker exec refugio-db-1 psql --username=refugio_user postgres \
    --command="DROP DATABASE refugio_prod;" \
    --command="CREATE DATABASE refugio_prod OWNER refugio_user;"

# 4. Restore backup
BACKUP="/opt/backups/refugio_prod_YYYY-MM-DD_HH-MM-SS.sql.gz"
gunzip -c "${BACKUP}" | docker exec --interactive refugio-db-1 \
    psql --username=refugio_user refugio_prod

# 5. Verify the restore
docker exec refugio-db-1 psql --username=refugio_user refugio_prod \
    --command="SELECT COUNT(*) FROM animals;" \
    --command="SELECT COUNT(*) FROM donors;" \
    --command="SELECT COUNT(*) FROM donations;"

# 6. Run Alembic migrations (in case backup predates latest migration)
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# 7. Restart application
docker compose -f docker-compose.prod.yml start api

# 8. Smoke test
curl https://sunstein.cloud/petShelter/health
```

---

## 5. Post-Restore Checklist

- [ ] Application health check passes: `curl https://sunstein.cloud/petShelter/health`
- [ ] Verify critical record counts match expectations
- [ ] Check application logs for errors: `docker logs refugio-api-1 --tail=50`
- [ ] Document the incident: date, cause, backup used, data loss window
- [ ] Notify team of any data loss period
- [ ] Review why the incident occurred and add preventive measures

---

## 6. Emergency Contacts

- **VPS access**: Hostinger VPS, sunstein.cloud
- **Backup location**: `/opt/backups/` on VPS
- **Application**: `/opt/refugio/`
- **Logs**: `/var/log/backup.log`, `docker logs refugio-api-1`

---

*Last updated: 2026-03-27*
