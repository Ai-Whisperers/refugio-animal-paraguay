# RAP-011 References

## Story & Task Specs
- `planning/epics/EPIC-9-deployment-and-infrastructure/stories/S02-ci-cd-pipeline/STORY.md`
- `planning/epics/EPIC-9-deployment-and-infrastructure/stories/S02-ci-cd-pipeline/tasks/T01-setup-test-pipeline.md`
- `planning/epics/EPIC-9-deployment-and-infrastructure/stories/S02-ci-cd-pipeline/tasks/T02-add-linting-checks.md`
- `planning/epics/EPIC-9-deployment-and-infrastructure/stories/S02-ci-cd-pipeline/tasks/T03-configure-deployment.md`

## Key Project Files
- `Makefile` — Quality gate targets (lint, type-check, format, test, security)
- `pyproject.toml` — Tool configuration (ruff, pyright, black, pytest)
- `Dockerfile` — Multi-stage build for deployment
- `docker-compose.yml` — Local dev services
- `.env.example` — Environment variable documentation

## Files Created/Modified
- `.github/workflows/ci.yml` — CI pipeline
- `.github/workflows/deploy.yml` — Deployment pipeline
- `.github/dependabot.yml` — Dependency updates
- `.env.example` — Updated with CI env vars
