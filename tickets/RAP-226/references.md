# RAP-226 References

## Key Files
- src/services/gdpr_third_party_deletion_service.py — NEW: third-party cascade
- src/services/gdpr_deletion_service.py — UPDATED: calls cascade
- src/schemas/gdpr_deletion.py — UPDATED: extended response
- src/db/models/subscription.py — SubscriptionStatus enum
- src/db/models/email_list.py — EmailListMember model
- src/db/models/donation.py — Donor.stripe_customer_id field
- tests/unit/test_gdpr_third_party_deletion_service.py — new unit tests
