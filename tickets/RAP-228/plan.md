# RAP-228 Plan

## Objective
Add GDPR erasure audit trail so every deletion request and confirmation is permanently recorded in the audit_logs table.

## Description
The GDPR deletion service processes personal data erasure but doesn't record the event in the audit trail. GDPR Article 5(2) (accountability principle) requires controllers to document data processing activities. This story adds audit trail recording at each stage of the deletion lifecycle: request initiation, confirmation, and admin-processed erasure.

## Acceptance Criteria
- [ ] `AuditAction.GDPR_ERASURE` added to audit_log enum
- [ ] Admin GDPR deletion (POST /gdpr/deletion-request) records audit entry with deletion summary
- [ ] Self-service deletion request (POST /portal/gdpr/delete) records audit entry at initiation
- [ ] Self-service deletion confirmation (POST /portal/gdpr/delete/confirm) records audit entry at confirmation
- [ ] All audit entries use resource_type="user" and record the anonymized user_id
- [ ] Unit tests updated to reflect new action count and value
- [ ] New unit tests for audit recording in deletion service

## Complexity Assessment
**Track**: Simple Fix — ≤4 files, ≤30 lines changed, clear pattern, no migration needed

**Assessment result**: Simple Fix — adds audit calls to existing functions, updates existing tests

## Approach
1. Add `GDPR_ERASURE = "gdpr_erasure"` to `AuditAction` enum
2. Update `gdpr_deletion_service.process_deletion_request()` to call `record_audit()`
3. Update `profile_service.request_account_deletion()` to call `record_audit()`
4. Update `profile_service.confirm_account_deletion()` to call `record_audit()`
5. Update `tests/unit/test_audit_model.py` for new action count
6. Add unit tests in `tests/unit/test_gdpr_deletion_audit.py`

## Dependencies
- Depends on: RAP-225 (S1), RAP-226 (S2) — DONE

## Risks
- Risk: AuditLog requires user_id FK — user record exists after anonymization (just deactivated), so FK remains valid. No issue.
