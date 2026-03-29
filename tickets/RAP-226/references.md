# RAP-226 References

## Key Files
- `src/services/gdpr_third_party_deletion_service.py` — NEW: third-party cascade service
- `src/services/gdpr_deletion_service.py` — updated: pre-fetch donor data, call cascade before anonymize
- `src/schemas/gdpr_deletion.py` — GDPRDeletionResponse extended with cascade summary fields
- `src/db/models/subscription.py` — SubscriptionStatus enum (CANCELED single L)
- `src/db/models/email_list.py` — EmailListMember model
- `tests/unit/test_gdpr_third_party_deletion_service.py` — 17 unit tests
- `tests/unit/test_gdpr_deletion_service.py` — updated test_full_deletion_request mock

## PR
- PR #351: feature/RAP-226-gdpr-third-party-deletion-cascade → develop

## Epic
- EPIC-46-gdpr-right-to-erasure/stories/S2-third-party-deletion-cascade-stripe-email/STORY.md
