---
story: S01
epic: EPIC-71
ticket: RAP-400
title: "Add test + lint pipeline to GitHub Actions"
status: ready
points: 5
priority: P0
track: DevOps
sprint: priority
version: V3.1
created: 2026-03-27
---

# S01: Add test + lint pipeline to GitHub Actions

## Story
As a **developer**, I want **automated tests and linting to run before every deployment** so that **broken code never reaches production**.

## Description
The current `.github/workflows/deploy.yml` deploys directly to production on push to `develop` with zero quality checks. This story adds a `test` job that must pass before the `deploy` job runs. The test job runs ruff (linting), pyright (type checking), and pytest (unit + integration tests) using a PostgreSQL service container.

## Acceptance Criteria

**Given** a push to the `develop` branch
**When** GitHub Actions triggers the deploy workflow
**Then** the following checks run BEFORE deployment:
- [ ] `ruff check src/ tests/` passes with zero warnings
- [ ] `pyright src/` passes with zero type errors
- [ ] `pytest tests/unit/ -x -q` passes (all 627+ unit tests)
- [ ] `pytest tests/integration/ -x -q` passes (all 360+ integration tests) using a PostgreSQL 16 service container
- [ ] If ANY check fails, deployment is BLOCKED (deploy job depends on test job)

**Given** a pull request to `develop`
**When** the PR is opened or updated
**Then** the same test + lint checks run as a PR status check

## Definition of Done
- [ ] `.github/workflows/deploy.yml` updated with `test` job before `deploy` job
- [ ] PostgreSQL 16 service container configured for integration tests
- [ ] `PYTHONPATH=.` set in test environment
- [ ] Deploy job has `needs: [test]` dependency
- [ ] PR status checks configured (tests must pass to merge)
- [ ] Tested by pushing a failing test and confirming deploy is blocked

## Technical Notes
- Epic: EPIC-71
- Track: DevOps
- Priority: P0 (CRITICAL — highest priority in entire backlog)
- File to modify: `.github/workflows/deploy.yml`
- Reference: Current workflow at `.github/workflows/deploy.yml` has deploy + health check only
- PostgreSQL service container: `services: { postgres: { image: postgres:16-alpine, env: { POSTGRES_USER: refugio_user, POSTGRES_PASSWORD: refugio_pass, POSTGRES_DB: refugio_test } } }`
- Set `DATABASE_URL=postgresql+asyncpg://refugio_user:refugio_pass@localhost:5432/refugio_test` in test env

## Story Points: 5
