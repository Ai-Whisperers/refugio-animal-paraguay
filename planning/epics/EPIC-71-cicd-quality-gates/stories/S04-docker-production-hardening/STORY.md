---
story: S04
epic: EPIC-71
ticket: RAP-403
title: "Harden Docker production image"
status: ready
points: 3
priority: P1
track: DevOps
sprint: priority
version: V3.1
created: 2026-03-27
---

# S04: Harden Docker production image

## Story
As a **system administrator**, I want **a lean, secure production Docker image** so that **the attack surface is minimized and image size is reduced**.

## Description
The current Dockerfile installs `[dev]` dependencies (pytest, ruff, pyright, bandit) into the runtime image. This bloats the image and exposes development tools in production. Fix the Dockerfile to only install production dependencies, increase uvicorn workers, and switch health checks from Python to curl.

## Acceptance Criteria
- [ ] Dockerfile pip install line uses `pip install .` instead of `pip install ".[dev]" .`
- [ ] Production image does NOT contain pytest, ruff, pyright, or bandit
- [ ] `curl` installed in runtime image for lightweight health checks
- [ ] Docker Compose health check uses `curl -f http://localhost:8000/health` instead of Python urllib
- [ ] Uvicorn workers default to `$(nproc)` instead of hardcoded 1
- [ ] Image size reduced by at least 30% compared to current

## Definition of Done
- [ ] `Dockerfile` updated (builder stage installs prod-only deps)
- [ ] `docker-compose.deploy.yml` health check updated to use curl
- [ ] `docker/entrypoint.sh` updated with dynamic worker count
- [ ] Image builds successfully and all tests pass in container
- [ ] Image size verified smaller than current

## Technical Notes
- Epic: EPIC-71
- Track: DevOps
- Priority: P1
- Files: `Dockerfile`, `docker-compose.deploy.yml`, `docker/entrypoint.sh`
- Current issue: Line 17 in Dockerfile does `pip install ".[dev]"`
- Worker formula: `UVICORN_WORKERS=${UVICORN_WORKERS:-$(nproc --all)}`

## Story Points: 3
