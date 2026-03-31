# RAP-226 Plan

## Objective
Implement third-party deletion cascade: notify and remove personal data from Stripe (cancel subscriptions, remove customer) and email lists when a GDPR deletion is processed.

## Description
GDPR Article 17 requires erasure not only from the shelter's own systems but also from processors who hold personal data on behalf of the controller. For Refugio Animal Paraguay, this includes Stripe (payment processor) and email service providers. This story adds a service layer that triggers third-party deletion as part of the GDPR deletion workflow.

## Acceptance Criteria
- [ ] `ThirdPartyDeletionService` cancels active Stripe subscriptions for a donor
- [ ] `ThirdPartyDeletionService` deletes Stripe customer record
- [ ] `ThirdPartyDeletionService` removes user from email lists (unsubscribes)
- [ ] Third-party cascade is called from `process_deletion_request()` when donor_id is provided
- [ ] Failures in third-party deletion are logged and included in summary — they must not raise
- [ ] API response includes `stripe_customer_deleted`, `email_lists_removed` fields
- [ ] Unit and integration tests passing

## Complexity Assessment
**Track**: Complex Implementation — multiple external API integrations, failure isolation, extended response schema

## Approach
1. Create `src/services/gdpr_third_party_deletion_service.py` with Stripe + email unsubscribe logic
2. Extend `process_deletion_request()` to call third-party cascade when applicable
3. Extend `GDPRDeletionResponse` with third-party status fields
4. Write unit tests with mocked external calls
5. Write integration tests verifying cascade is triggered

## Dependencies
- Depends on: RAP-225 (for process_deletion_request context) — implemented in parallel
- Stripe library already present (src/api/sepa.py, src/services/tigo_money_service.py check)
- Email list service: src/services/email_list_service.py, email_unsubscribe_service.py

## Risks
- Risk: Stripe API unavailable during deletion → Mitigation: catch exceptions, log, continue — include failure in summary
- Risk: Email provider API timeout → Mitigation: same pattern, never block deletion on third-party failure
