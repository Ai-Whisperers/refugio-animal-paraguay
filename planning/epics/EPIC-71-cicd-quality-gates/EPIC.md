---
epic: EPIC-71
title: "CI/CD Quality Gates"
status: ready
priority: 100
sprint: priority
version: V3.1
points: 21
created: 2026-03-27
---

# [EPIC-71] CI/CD Quality Gates

## Overview
**Goal**: Ensure no broken code reaches production by adding automated testing, security scanning, and staging verification to the deployment pipeline.
**Why it matters**: Currently, pushes to `develop` deploy directly to production with ZERO test execution. This is the single highest-risk gap in the entire system.
**Target users**: All users — broken deploys affect everyone.

## Scope
### In Scope
- Add pytest + ruff + pyright to GitHub Actions before deploy
- Add security scanning (bandit, pip-audit) to CI
- Create staging environment with approval gate
- Harden Docker production image (remove dev deps)
- Add coverage reporting and PR status checks

### Out of Scope
- E2E testing with Playwright (separate epic: EPIC-64)
- Performance testing (separate epic)
- Multi-environment secrets rotation

## Stories
- [ ] [S01] RAP-400: Add test + lint pipeline to GitHub Actions
- [ ] [S02] RAP-401: Add security scanning to CI
- [ ] [S03] RAP-402: Create staging environment with approval gate
- [ ] [S04] RAP-403: Harden Docker production image
- [ ] [S05] RAP-404: Add coverage reporting and PR status checks

## Dependencies
- None — this is foundational infrastructure
- Blocks: All future feature work should pass these gates

## Risks
- Risk: Tests that pass locally but fail in CI due to DB dependency → Mitigation: Use service containers in GitHub Actions for PostgreSQL
- Risk: Staging env adds hosting cost → Mitigation: Use same VPS with separate Docker Compose profile
