# RAP-011 Plan

## Objective
Create GitHub Actions CI/CD workflows for automated testing, linting, and deployment preparation.

## Description
The project has 204 tests, 80%+ coverage, and a full Makefile with quality gates — but no CI/CD automation. This ticket adds GitHub Actions workflows that enforce quality gates on every push/PR and automate deployment to staging and production via tag-based releases.

## Acceptance Criteria
- [ ] CI workflow runs lint (ruff), type-check (pyright), format-check (black), and tests on every push and PR
- [ ] Test job uses PostgreSQL 16 service container with test credentials
- [ ] Coverage threshold (80%) enforced in CI with artifact upload (coverage + JUnit XML)
- [ ] Deployment workflow triggers on main merge and release tags
- [ ] Deployment workflow includes Docker image build, smoke test placeholders, and manual approval gate for production
- [ ] Dependabot configured for Python dependency updates
- [ ] .env.example documents all CI-required environment variables
- [ ] All existing tests continue to pass
- [ ] Zero lint warnings in new workflow files

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A, new feature
- [x] Solution affects <=3 files — No, 4+ new files
- [ ] Change impact <=10 lines of actual code — No, significant YAML
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — Multiple new workflow files, service containers, environment configuration, and deployment gates.

## Approach
1. Create `.github/workflows/ci.yml` with lint -> type-check -> format-check -> test pipeline
2. Create `.github/workflows/deploy.yml` with test -> build -> smoke -> deploy pipeline
3. Create `.github/dependabot.yml` for automated dependency PRs
4. Update `.env.example` with CI-specific variable documentation
5. Validate all existing quality gates still pass

## Dependencies
- Depends on: RAP-010 (Docker setup — completed)
- Blocked by: Nothing

## Risks
- Risk: Pyright may behave differently in CI vs local → Mitigation: Pin pyright version, use same Python 3.12
- Risk: PostgreSQL service container connection issues → Mitigation: Use standard GitHub Actions service container pattern
