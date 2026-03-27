# RAP-400 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-27 00:00

## Current Focus
Creating .github/workflows/ci.yml with test + lint quality gates.

## Technical State
- Existing: .github/workflows/deploy.yml (deploy-only, no quality gates)
- Target: New ci.yml workflow with ruff, black, pytest (unit only)
- No DB needed for unit tests (uses mocks/fixtures)

## Next Steps
1. Write .github/workflows/ci.yml
2. Commit and push
3. Create PR

## Blockers
None

## Key Decisions Made
- Skip integration tests in CI (require live DB not available in GitHub Actions without extra setup)
- Use pytest -m "not integration" to exclude integration tests
