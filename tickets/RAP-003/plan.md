# RAP-003 Plan

## Objective
Scaffold the FastAPI application layer: settings module, database session factory, app entrypoint, and a `/health` endpoint that verifies DB connectivity.

## Description
With the database schema validated (RAP-001/002), the next layer is the FastAPI application shell. This ticket wires together: a Pydantic-settings config module (reads from env vars), a SQLAlchemy async session factory, a FastAPI `app` instance with lifespan, and a `/health` check endpoint that returns DB status. No domain routes yet — only the plumbing that all future endpoints depend on.

## Acceptance Criteria
- [ ] `src/config.py` — Pydantic `Settings` class reads `DATABASE_URL`, `APP_ENV`, `DEBUG` from env
- [ ] `src/db/session.py` — async SQLAlchemy engine + `AsyncSession` factory; `get_db` FastAPI dependency
- [ ] `src/app.py` — FastAPI app with lifespan that opens/closes DB engine
- [ ] `GET /health` returns `{"status": "ok", "db": "connected"}` when DB is reachable
- [ ] `GET /health` returns HTTP 503 + `{"status": "degraded", "db": "unreachable"}` when DB is down
- [ ] Tests: unit tests for Settings, integration test for `/health` endpoint
- [ ] `pyproject.toml` updated with `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg` deps
- [ ] Zero Pyright warnings on new files

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A (new feature)
- [ ] Solution affects ≤3 files — NO (6+ files)
- [ ] Change impact ≤10 lines of actual code — NO
- [ ] Low risk of side effects — Medium (touching db engine config)
- [ ] Solution pattern is well-understood — YES

**Assessment**: Complex — multiple new files, async SQLAlchemy + FastAPI wiring, integration test requires live DB.

## Approach

### Phase 1: Dependencies
- Add `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `sqlalchemy[asyncio]`, `asyncpg` to `pyproject.toml`
- Install into venv

### Phase 2: Settings module
- `src/config.py` — `Settings(BaseSettings)` with `DATABASE_URL`, `APP_ENV`, `DEBUG`
- Unit test: override via env vars, default values, validation

### Phase 3: Session factory
- `src/db/session.py` — `create_async_engine`, `async_sessionmaker`, `get_db` dependency
- Wires DATABASE_URL from `Settings`

### Phase 4: App entrypoint + health route
- `src/app.py` — FastAPI lifespan, router include, CORS stub
- `src/api/health.py` — `/health` router with DB ping

### Phase 5: Tests
- `tests/unit/test_config.py` — Settings env override
- `tests/integration/test_health.py` — `/health` happy path and DB-down scenario

## Dependencies
- Depends on: RAP-001 (schema), RAP-002 (ORM models) — both complete
- Blocked by: nothing

## Risks
- Async SQLAlchemy + psycopg2 incompatibility → Mitigation: use `asyncpg` driver for async, keep `psycopg2-binary` for Alembic sync operations
- Pyright struggles with SQLAlchemy async types → Mitigation: use explicit type annotations, `# type: ignore` sparingly with comments
