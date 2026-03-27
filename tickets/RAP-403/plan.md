# RAP-403 Plan

## Objective
Harden the Docker production image: non-root user, minimal attack surface, health checks, proper build stages.

## Acceptance Criteria
- [ ] Backend container runs as non-root user
- [ ] Builder stage installs only runtime deps (not dev deps)
- [ ] HEALTHCHECK instruction added to backend Dockerfile
- [ ] docker-compose.deploy.yml adds security_opt: no-new-privileges:true
- [ ] docker-compose.deploy.yml adds resource limits (memory)
- [ ] All existing tests still pass

## Complexity Assessment
**Track**: Simple Fix — 2 files modified, well-understood Docker hardening patterns

## Approach
1. Dockerfile: Add non-root user (appuser), fix builder to install runtime only, add HEALTHCHECK
2. docker-compose.deploy.yml: Add security_opt, mem_limit
