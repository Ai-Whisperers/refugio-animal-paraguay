# RAP-229 Plan

## Objective
Implement data retention policy automation to periodically purge expired and used verification tokens, enforcing GDPR Article 5(1)(e) storage limitation.

## Description
GDPR Article 5(1)(e) requires that personal data not be kept longer than necessary. Verification tokens (password reset, email verification, account deletion) accumulate in the database and contain enough information to identify users. A data retention service purges these expired/used tokens according to configurable retention periods, and exposes an admin endpoint to trigger cleanup on-demand (to be called by a cron job or n8n workflow in production).

## Acceptance Criteria
- [ ] `DataRetentionService` in `src/services/data_retention_service.py` with configurable retention periods
- [ ] Purges expired unused verification tokens after EXPIRED_TOKEN_RETENTION_DAYS (default: 30)
- [ ] Purges used verification tokens after USED_TOKEN_RETENTION_DAYS (default: 90)
- [ ] Returns a `DataRetentionResult` summary with counts of deleted records by category
- [ ] Admin API endpoint `POST /admin/data-retention/run` triggers retention cleanup
- [ ] Endpoint requires admin auth
- [ ] Unit tests covering all cleanup paths and result reporting
- [ ] No migration needed (operates on existing tables)

## Complexity Assessment
**Track**: Simple Fix — 2 new files (service + admin endpoint) + tests, no migration, well-understood pattern

**Assessment result**: Simple Fix — new service and endpoint following existing patterns

## Approach
1. Create `src/services/data_retention_service.py`
2. Create `src/api/admin_data_retention.py`
3. Register router in `src/app.py`
4. Create `tests/unit/test_data_retention_service.py`

## Dependencies
- Depends on: RAP-225, RAP-226 — DONE

## Risks
- Risk: deleting tokens used by active sessions → Mitigation: only delete tokens with used_at or expires_at in the past beyond retention window
