# RAP-400 Plan

## Objective
Add test + lint quality gates to GitHub Actions CI pipeline so every PR is validated before deploy.

## Description
The current GitHub Actions only has a `deploy.yml` that deploys to production on every `develop` push — with zero quality checks. This means broken code, failing tests, and lint errors can be deployed to production. We need a `ci.yml` workflow that runs on PRs and pushes to `develop` and `main` to enforce quality gates.

## Acceptance Criteria
- [ ] CI runs on every PR targeting develop or main
- [ ] CI runs on push to develop and main
- [ ] Ruff linting is enforced (zero warnings)
- [ ] Black formatting is checked
- [ ] All tests run (unit tests only, no DB needed for unit)
- [ ] CI fails fast on any gate failure
- [ ] Test results visible in PR checks

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified — no CI workflow exists
- [x] Solution affects ≤3 files — one new .github/workflows/ci.yml
- [x] Change impact ≤10 lines of actual code — ~60 lines of YAML
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple Fix — add a new workflow file, no existing code modified

## Approach
Create `.github/workflows/ci.yml` with:
1. Trigger on PR (develop, main) and push (develop, main)
2. Python setup with pip cache
3. Install dev dependencies
4. Run ruff check
5. Run black --check
6. Run pytest unit tests (skip integration — no DB in CI)

## Dependencies
- Depends on: None
- Blocked by: Nothing

## Risks
- Risk: Integration tests require a live DB → Mitigation: Skip integration with `-m "not integration"` marker
