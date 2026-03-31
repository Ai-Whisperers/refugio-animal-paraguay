# RAP-241 Plan

## Objective
Add an automated, scheduled dependency vulnerability scanning workflow that hard-fails on known CVEs and creates a GitHub Issue when new vulnerabilities are discovered between push cycles.

## Acceptance Criteria
- [x] pip-audit runs on every PR and push to develop/main (hard-fail mode)
- [x] pip-audit runs on a weekly cron schedule (Monday 08:00 UTC)
- [x] Workflow creates/updates a GitHub Issue when scheduled scan finds vulnerabilities
- [x] .pip-audit-ignore file allows suppressing known false positives with required comments
- [x] Audit report uploaded as workflow artifact (30-day retention)
- [x] Old security.yml pip-audit step (soft-fail) removed

## Complexity Assessment
**Track**: Simple Fix — new workflow file + config file + tests, no Python src changes

## Approach
1. Create `.github/workflows/dependency-scan.yml` with PR/push + weekly schedule
2. Create `.pip-audit-ignore` for known suppressions with format validation
3. Update `security.yml` to remove redundant soft-fail pip-audit step
4. Write tests validating workflow config and ignore file format
