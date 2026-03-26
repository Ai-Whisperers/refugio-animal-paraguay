# RAP-003 Recap

## Outcome

Delivered all planned components: Settings module, async session factory, FastAPI app with lifespan, and health-check endpoint. All acceptance criteria met.

## Acceptance Criteria — Final Status

- [x] `src/config.py` — Pydantic Settings with DATABASE_URL/APP_ENV/DEBUG, field validation, asyncpg enforcement
- [x] `src/db/session.py` — async SQLAlchemy engine + AsyncSession factory + `get_db` dependency
- [x] `src/app.py` — FastAPI app with lifespan managing DB engine lifecycle
- [x] `src/api/health.py` — GET /health returns `{"status": "ok", "db": "connected"}` or 503/degraded
- [x] `tests/unit/test_config.py` — 13 unit tests for Settings class
- [x] `tests/integration/test_health.py` — 2 integration tests (happy path + DB unreachable)
- [x] Zero Pyright errors/warnings (`venv/bin/pyright src/ tests/` → 0/0/0)
- [x] All 45 tests passing

## Key Learnings

- **Two-Postgres problem**: Host PostgreSQL 16 service owns `127.0.0.1:5432` (IPv4). Docker `shared-postgres` (host-network mode) is only reachable via `[::1]:5432` (IPv6 loopback). All database URLs must use `[::1]` in this environment.
- **asyncpg vs psycopg2 split**: Alembic requires sync driver (psycopg2-binary); FastAPI async routes require asyncpg. Both coexist — different URL schemes for different use cases.
- **Pyright venv resolution**: `pyrightconfig.json` needs explicit `venvPath`/`venv` to resolve installed packages; `extraPaths` alone is insufficient.
- **setuptools build backend**: Must use `setuptools.build_meta`, not `setuptools.backends.legacy:build`.

## Follow-Up Actions

- [ ] RAP-004: Animals CRUD API routes
- [ ] RAP-005: Adopters CRUD API routes
- [ ] RAP-006: Adoption requests workflow API

## Validation Evidence

- Tests: 45 passing, 0 failing
- Pyright: 0 errors, 0 warnings, 0 informations
- Linting: clean
- Coverage: unit tests 100% for config module; integration tests cover both health states
