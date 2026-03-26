# RAP-010 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26

## Current Focus
Ticket closed. Docker containerization complete and verified.

## Technical State
- Dockerfile: multi-stage (builder → runtime), python:3.12-slim
- docker-compose.yml: api + db, health checks, volume persistence
- docker/entrypoint.sh: POSIX sh-compatible URL stripping via sed
- btree_gist extension added to migration 001 (required for GIST EXCLUDE on UUID)
- stripe added to pyproject.toml prod dependencies

## Key Decisions Made
- Used `sed` instead of bash `${var/find/replace}` — python:3.12-slim uses dash (POSIX sh), not bash
- btree_gist must be enabled before the GIST exclusion constraint on adoption_requests
- .env.example blocked by hook; env vars documented inline in docker-compose.yml with defaults
