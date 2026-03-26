# RAP-001 References

## Ticket Files
- `plan.md` — Objective, acceptance criteria, complexity assessment
- `context.md` — Current focus, technical state, next steps (live document)
- `progress.md` — Append-only action log
- `timeline.md` — Session tracking and durations
- `recap.md` — Outcome summary (created at closure)

## Related Tickets
- None yet (initial ticket in project)

## Tech Stack & Architecture
- **ADR-001**: Core tech stack decision — PostgreSQL 16, SQLAlchemy 2.x, Alembic migrations
- **Project CLAUDE.md**: Refugio conventions (UUIDs, TIMESTAMPTZ, snake_case, status enums)

## Skills & Agents
- `.claude/agents/schema-designer.md` — Validates table definitions against conventions
- `.claude/skills/postgresql-patterns.md` — Schema design, indexing, migrations, query optimization
- `.claude/skills/testing-patterns.md` — Writing tests for database schema changes

## Domain Resources
- **PostgreSQL 16 Documentation**: https://www.postgresql.org/docs/16/
  - EXCLUDE constraints: https://www.postgresql.org/docs/16/sql-createtable.html#SQL-CREATETABLE-EXCLUDE
  - Indexes: https://www.postgresql.org/docs/16/sql-createindex.html
  - UUID type: https://www.postgresql.org/docs/16/datatype-uuid.html
  - TIMESTAMPTZ: https://www.postgresql.org/docs/16/datatype-datetime.html

- **Alembic Documentation**: https://alembic.sqlalchemy.org/
  - Migrations: https://alembic.sqlalchemy.org/en/latest/tutorial.html
  - Naming conventions: https://alembic.sqlalchemy.org/en/latest/naming.html

- **SQLAlchemy 2.x Documentation**: https://docs.sqlalchemy.org/en/20/
  - Column types: https://docs.sqlalchemy.org/en/20/core/types.html
  - Constraints: https://docs.sqlalchemy.org/en/20/core/constraints.html

## Project Rules
- `.claude/rules/ticket-management.md` — Ticket lifecycle, validation, completion
- `.claude/rules/quality-standards.md` — Zero warnings/errors, diagnostic standards
- `.claude/rules/testing.md` — Test coverage, unit/integration/E2E pyramid
- `.claude/rules/git-workflow.md` — Branch naming, commit standards

## Key Conventions
**Refugio Database Conventions**:
- Primary Keys: UUID, column name `id`
- Timestamps: TIMESTAMPTZ with timezone awareness, columns `created_at`, `updated_at`
- Naming: snake_case for tables and columns
- Status Pattern: VARCHAR with CHECK constraint (not soft-delete with deleted_at)
- Foreign Keys: Explicit constraint with ON DELETE CASCADE or SET NULL
- Indexes: On status, FK columns, query-critical columns
- GDPR: Explicit consent timestamp (`gdpr_consent_at`) for adopters table

**Database Tiers**:
- Development: `refugio_dev` (local)
- Staging: `refugio_staging` (staging)
- Production: `refugio_prod` (production)

## Implementation Phases
1. **Schema Design** ← Current phase (schema-designer agent validation)
2. **Alembic Migration** ← Write migration file descriptively named
3. **Seed Data** ← 5 sample animals + 2 adopters for testing

## Key Decisions
- Status VARCHAR with CHECK constraint initially (risk mitigation for unknown status values)
- Will migrate to native PostgreSQL enum type once status requirements stabilize
- EXCLUDE constraint on adoption_requests to prevent duplicate pending requests per animal
- Minimal seed data (5+2) sufficient for testing adoption workflow

## Blocker Status
None — ready to proceed with schema-designer agent validation.
