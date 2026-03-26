# RAP-040 Plan

## Objective
Implement GDPR Article 17 data deletion (right to erasure) with approval workflow and data anonymization.

## Acceptance Criteria
- [x] DeletionRequest model with status lifecycle
- [x] POST /gdpr/deletion-requests creates pending request
- [x] GET /gdpr/deletion-requests lists requests with status filter
- [x] POST /gdpr/deletion-requests/{id}/approve executes deletion (admin only)
- [x] POST /gdpr/deletion-requests/{id}/deny denies with reason (admin only)
- [x] POST /gdpr/deletion-requests/{id}/cancel cancels pending request
- [x] Donor deletion: anonymize donations (null FK), hard-delete profile
- [x] Adopter deletion: anonymize adoption requests (null FK), hard-delete profile
- [x] Staff deletion: anonymize email/password, deactivate account
- [x] Unit tests for lifecycle and anonymization logic
- [x] Integration tests for API endpoints

## Complexity Assessment
**Track**: Complex — approval workflow, three subject types, anonymization vs deletion logic

## Approach
1. DeletionRequest model with approval workflow status machine
2. Anonymization service per subject type
3. API endpoints with role-based access (admin for approve/deny)
4. Comprehensive tests
