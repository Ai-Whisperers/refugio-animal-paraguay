# RAP-401 Plan

## Objective
Add security scanning (bandit SAST + pip-audit dependency vulnerability scan) to the GitHub Actions CI pipeline.

## Description
The CI pipeline (RAP-400) now enforces lint and tests. We need a second stage: security scanning. Bandit catches common Python security issues (SQL injection, hardcoded passwords, unsafe subprocess, etc). Pip-audit checks for known CVEs in dependencies. Both should block the pipeline on critical/high findings.

## Acceptance Criteria
- [ ] bandit SAST scan runs on src/ on every PR
- [ ] pip-audit dependency vulnerability scan runs on every PR
- [ ] Pipeline fails on bandit HIGH/CRITICAL severity findings
- [ ] Pipeline fails on pip-audit HIGH/CRITICAL CVEs
- [ ] Security scan results uploaded as artifact

## Complexity Assessment
**Track**: Simple Fix
**Assessment result**: Simple Fix — add security job to existing ci.yml + fix any bandit findings in src/

## Approach
1. Add `security` job to `.github/workflows/ci.yml`
2. Run `bandit -r src/ -ll` (LOW severity threshold for now, fail on MEDIUM+)
3. Run `pip-audit --fix-auto=false --desc`
4. Fix any bandit issues found in src/

## Dependencies
- Depends on: RAP-400 (CI pipeline exists)
- Blocked by: Nothing

## Risks
- Risk: bandit may flag legitimate code patterns → Mitigation: use `-ll` (MEDIUM+) threshold, not LOW
