---
story: S02
epic: EPIC-71
ticket: RAP-401
title: "Add security scanning to CI"
status: ready
points: 3
priority: P0
track: DevOps
sprint: priority
version: V3.1
created: 2026-03-27
---

# S02: Add security scanning to CI

## Story
As a **shelter administrator**, I want **automated security scanning in the CI pipeline** so that **vulnerable dependencies and insecure code patterns are caught before deployment**.

## Description
Add `bandit` (static analysis for Python security issues) and `pip-audit` (dependency vulnerability scanner) to the GitHub Actions test job. Both tools are already in `pyproject.toml` dev dependencies but are never run in CI.

## Acceptance Criteria
- [ ] `bandit -r src/ -c pyproject.toml` runs in CI and fails on HIGH/CRITICAL findings
- [ ] `pip-audit` runs in CI and fails on known HIGH/CRITICAL vulnerabilities
- [ ] Results are posted as annotations on PR (or at minimum visible in CI logs)
- [ ] Existing codebase passes both scans (fix any current findings first)
- [ ] Security scan step runs AFTER lint but BEFORE tests (fail fast)

## Definition of Done
- [ ] Security scan step added to `.github/workflows/deploy.yml` test job
- [ ] Any existing bandit findings in `src/` resolved or explicitly suppressed with `# nosec` + justification
- [ ] Any existing pip-audit findings resolved or documented as accepted risk
- [ ] CI blocks deployment on new HIGH/CRITICAL findings

## Technical Notes
- Epic: EPIC-71
- Track: DevOps
- Priority: P0
- Tools: `bandit>=1.7`, `pip-audit>=2.7` (already in pyproject.toml)
- Bandit config can go in `pyproject.toml` under `[tool.bandit]`

## Story Points: 3
