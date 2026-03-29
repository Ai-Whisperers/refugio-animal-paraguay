# RAP-226 Plan

## Objective
Implement GDPR Article 17(2) third-party cascade: cancel Stripe subscriptions, delete Stripe customer record, and hard-delete email list memberships when a donor's data is erased.

## Description
GDPR Article 17(2) requires notifying processors when erasure is requested. For donors this means: cancelling active Stripe subscriptions, deleting the Stripe customer record, and hard-deleting EmailListMember records. Third-party failures must not block the core anonymization — log-don't-raise pattern.

## Acceptance Criteria
- [x] `cancel_active_stripe_subscriptions()` cancels ACTIVE/PAST_DUE subscriptions via Stripe API, updates local status, returns {cancelled, failed, skipped}
- [x] `delete_stripe_customer()` deletes Stripe customer object, returns bool
- [x] `remove_from_email_lists()` hard-deletes EmailListMember records by email, skips anonymized/empty emails
- [x] `process_third_party_deletion()` orchestrates all three with no Stripe key graceful skip
- [x] Third-party cascade called BEFORE donor anonymization (email/stripe_id captured first)
- [x] Third-party failures are caught and logged, not raised (isolation)
- [x] Summary includes: stripe_subscriptions_cancelled, stripe_subscriptions_failed, stripe_customer_deleted, email_lists_removed
- [x] GDPRDeletionResponse updated with cascade summary fields
- [x] 17 unit tests covering all code paths
- [x] All quality gates pass

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new service module, external API integration, pre-fetch ordering requirement, log-don't-raise isolation pattern.

## Approach
1. Create src/services/gdpr_third_party_deletion_service.py
2. Implement three deletion functions with proper isolation
3. Update process_deletion_request() to call cascade before anonymizing donor
4. Update GDPRDeletionResponse schema
5. Write 17 unit tests
6. Run quality gates

## Dependencies
- Depends on: RAP-225 (base deletion service)
- Blocks: nothing (this completes EPIC-46 P0 stories)

## Risks
- Stripe API key missing in test/staging → Mitigation: _get_stripe_key() returns None, all Stripe calls skip gracefully
- Third-party failure during deletion → Mitigation: log-don't-raise, deletion continues regardless
