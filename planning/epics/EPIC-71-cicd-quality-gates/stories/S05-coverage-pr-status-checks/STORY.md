---
story: S05
epic: EPIC-71
ticket: RAP-404
title: "Add coverage reporting and PR status checks"
status: ready
points: 5
priority: P2
track: DevOps
sprint: priority
version: V3.1
created: 2026-03-27
---

# S05: Add coverage reporting and PR status checks

## Story
As a **developer**, I want **coverage reports posted on PRs and status checks that block merging below threshold** so that **test coverage never decreases**.

## Description
Add `pytest-cov` coverage reporting to the CI pipeline. Post coverage summaries as PR comments using a GitHub Action. Block PRs from merging if coverage drops below 80% overall or new code has less than 80% coverage.

## Acceptance Criteria
- [ ] `pytest --cov=src --cov-report=xml --cov-fail-under=80` runs in CI
- [ ] Coverage report posted as PR comment with per-file breakdown
- [ ] PRs blocked from merging if overall coverage drops below 80%
- [ ] Coverage XML artifact uploaded for trend tracking
- [ ] Branch protection rules updated to require coverage check

## Definition of Done
- [ ] Coverage step added to test job in `.github/workflows/deploy.yml`
- [ ] Coverage comment action configured (e.g., `py-cov-action/python-coverage-comment-action`)
- [ ] `--cov-fail-under=80` enforced
- [ ] Branch protection rules on `develop` updated
- [ ] Tested with a PR that reduces coverage (should block merge)

## Technical Notes
- Epic: EPIC-71
- Track: DevOps
- Priority: P2
- Coverage config in `pyproject.toml` or `.coveragerc`
- Existing coverage: ~80% (tight — need to be careful not to drop)

## Story Points: 5
