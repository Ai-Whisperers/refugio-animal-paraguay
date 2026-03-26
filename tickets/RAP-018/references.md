# RAP-018 References

## Key Files
- `src/db/models/audit_log.py` — AuditLog ORM model (new)
- `src/audit/middleware.py` — FastAPI audit middleware (new)
- `src/api/audit_logs.py` — Query/export API endpoints (new)
- `src/schemas/audit_log.py` — Pydantic schemas (new)
- `src/db/alembic/versions/005_create_audit_log_table.py` — Migration (new)
- `src/events/base.py` — Event bus (existing, RAP-017)
- `src/auth/dependencies.py` — JWT auth deps (existing)

## Story
- `planning/epics/EPIC-13-impact-and-compliance/stories/S01-audit-trail-system/STORY.md`
