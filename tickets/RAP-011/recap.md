# RAP-011 Recap

## Outcome
Delivered GitHub Actions CI/CD pipeline with two workflows:

1. **CI workflow** (`ci.yml`) — Runs on every push and PR with sequential jobs: lint (ruff) -> type-check (pyright) + format-check (black) -> test (pytest + PostgreSQL 16 service container) + security (bandit + pip-audit). Coverage threshold enforced at 80%. Artifacts uploaded for coverage and JUnit XML reports.

2. **Deployment workflow** (`deploy.yml`) — Triggers on main merge and release tags. Stages: verify tests -> build and push Docker image to GHCR -> deploy staging (automatic) -> deploy production (manual approval via GitHub Environments). Smoke test placeholders for /health and /animals endpoints.

3. **Dependabot** (`dependabot.yml`) — Weekly automated PRs for pip and GitHub Actions dependency updates.

4. **Environment documentation** — `.env.example` updated with CI/CD variable documentation including GitHub Environments secrets and variables.

## Acceptance Criteria -- Final Status
- [x] CI workflow runs lint, type-check, format-check, and tests on every push and PR
- [x] Test job uses PostgreSQL 16 service container with test credentials
- [x] Coverage threshold (80%) enforced in CI with artifact upload
- [x] Deployment workflow triggers on main merge and release tags
- [x] Deployment workflow includes Docker image build, smoke test placeholders, and manual approval gate
- [x] Dependabot configured for Python dependency updates
- [x] .env.example documents all CI-required environment variables
- [x] All existing tests continue to pass (204 passed)
- [x] Zero new lint warnings introduced

## Key Learnings
- Pre-existing lint (ruff) and format (black) issues exist in codebase (98 ruff errors, 19 files need black formatting). CI will initially fail on these — a separate cleanup ticket is needed.
- pip-audit in CI is valuable for catching vulnerable dependencies early.

## Validation Evidence
- Tests: 204 passing, 0 failing (27.38s)
- YAML syntax: Valid (no syntax errors in workflow files)
- Pre-existing issues: 98 ruff lint errors, 19 files need black formatting (not introduced by this PR)
- Coverage: 80.42% (above 80% threshold)
