# RAP-010 Recap

## Outcome
Docker containerization delivered as planned. Full stack (FastAPI + PostgreSQL) starts with `docker compose up`.

## Acceptance Criteria — Final Status
- [x] Dockerfile — multi-stage build; final image runs uvicorn, no dev deps
- [x] docker-compose.yml — services: api, db (postgres:16); volumes for data persistence
- [x] .dockerignore — excludes venv, __pycache__, .env, tickets, etc.
- [x] `docker compose up` starts the stack; health endpoint returns 200
- [x] Alembic migrations run automatically on container start (all 4 migrations applied)
- [x] `docker compose down -v` cleanly removes state
- [ ] .env.example — BLOCKED by pre_tool_use hook; env vars documented in docker-compose.yml inline

## Key Learnings
- `${var/find/replace}` is a bash-only substitution — does not work in POSIX sh (dash). `sed` is the portable alternative.
- `btree_gist` extension must be enabled before any GIST exclusion constraint on non-geometric types (UUID, int, etc.)
- `pip install --prefix=/install` in multi-stage builder, then `COPY --from=builder /install /usr/local` in runtime stage cleanly separates build and runtime layers.

## Validation Evidence
- Docker build: clean (no errors)
- `docker compose up`: all 4 migrations applied, uvicorn started
- `GET /health`: `{"status": "ok", "db": "connected"}` returned 200
- `docker compose down -v`: containers, network, and volume removed cleanly
- Tests: 204 passed, 0 failed (migration change non-breaking)
