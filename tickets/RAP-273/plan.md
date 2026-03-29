# RAP-273 Plan

## Objective
Backend service and API endpoint for detecting suspicious activity patterns in the audit log.

## Acceptance Criteria
- [ ] detect_suspicious_activity() service scans for: bulk deletes, bulk exports, GDPR erasure bursts, high-frequency activity
- [ ] GET /admin/security/suspicious-activity returns structured alert report
- [ ] Configurable look-back window (default 60 min, max 24h)
- [ ] 10 unit tests passing

## Complexity Assessment
**Track**: Simple Fix — new service + thin API router, no schema migrations needed
