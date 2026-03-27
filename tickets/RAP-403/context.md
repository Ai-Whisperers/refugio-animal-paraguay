# RAP-403 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-27

## Key Decisions Made
- Non-root user (appuser uid=1001) added to backend Dockerfile
- Builder stage now installs only runtime deps (removed "[dev]" install)
- HEALTHCHECK added using /health endpoint (already exists)
- curl added to runtime image for health checks
- docker-compose.deploy.yml: security_opt no-new-privileges, mem_limit 512m API / 256m frontend
