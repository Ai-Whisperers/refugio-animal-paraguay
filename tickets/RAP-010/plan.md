# RAP-010 Plan

## Objective
Containerize the Refugio Animal Paraguay API so the full stack (FastAPI + PostgreSQL) can be started with `docker compose up`.

## Acceptance Criteria
- [ ] `Dockerfile` — multi-stage build; final image runs uvicorn, no dev deps
- [ ] `docker-compose.yml` — services: `api`, `db` (postgres:16); volumes for data persistence
- [ ] `.env.example` — all required env vars documented
- [ ] `.dockerignore` — excludes venv, __pycache__, .env, tickets, etc.
- [ ] `docker compose up` starts the stack; health endpoint returns 200
- [ ] Alembic migrations run automatically on container start
- [ ] `docker compose down -v` cleanly removes state

## Complexity Assessment
**Track**: Simple Fix — well-understood pattern, ≤4 new files, no business logic changes

**Assessment**: Simple — standard FastAPI containerization pattern with entrypoint script for migrations

## Approach
1. Dockerfile (multi-stage: builder → runtime)
2. entrypoint.sh (run alembic upgrade head, then uvicorn)
3. docker-compose.yml (api + db services)
4. .env.example
5. .dockerignore

## Dependencies
- Depends on: RAP-007, RAP-008, RAP-009 (all complete)

## Risks
- Risk: IPv6 DB URL in config won't work inside Docker bridge network → Mitigation: docker-compose sets DATABASE_URL env var to use hostname `db`
