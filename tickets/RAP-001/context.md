# RAP-001 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-25 21:15

## Current Focus
Schema design for core tables: animals, adopters, adoption_requests. Following Refugio conventions (UUIDs, TIMESTAMPTZ, snake_case, status enums).

## Technical State
- Tech stack: PostgreSQL 16, SQLAlchemy 2.x, Alembic migrations (from ADR-001)
- Database: refugio_dev (local), refugio_staging (staging), refugio_prod (production)
- Naming: UUIDs for all PKs, TIMESTAMPTZ for all timestamps, snake_case tables/columns
- Status pattern: status enums (not soft-delete with deleted_at), status changes track lifecycle
- GDPR: adopters table includes gdpr_consent_at timestamp
- Constraints: EXCLUDE constraint on adoption_requests to prevent duplicate active requests per animal

## Next Steps
1. Invoke schema-designer agent to validate schema design (animals, adopters, adoption_requests tables)
2. Create Alembic migration file (named descriptively per Refugio conventions)
3. Create seed data script (5 sample animals + 2 adopters)
4. Validate schema against conventions (UUIDs, TIMESTAMPTZ, snake_case)
5. Run acceptance criteria checklist

## Blockers
None currently.

## Key Decisions Made
- Status enums over soft-delete: Use VARCHAR with check constraint initially, migrate to proper enum once stable (risk mitigation from plan)
- EXCLUDE constraint approach: Prevents duplicate pending requests on same animal
- Seed data scope: 5 animals + 2 adopters (minimal viable set for testing)

## RESUME POINT
Ready to begin schema design phase. Next: invoke schema-designer agent from .claude/agents/ to validate table definitions before writing Alembic migration.
