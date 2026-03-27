# RAP-153 Plan

## Objective
Add GET /donations/{id}/sepa-status endpoint for tracking async SEPA payment lifecycle.

## Acceptance Criteria
- [ ] GET /donations/{id}/sepa-status returns local + Stripe status
- [ ] is_sepa flag distinguishes SEPA from other payment methods
- [ ] is_processing flag indicates SEPA awaiting bank settlement
- [ ] stripe_status from live Stripe API (graceful degradation on error)
- [ ] 404 for unknown donation
- [ ] 3 integration tests

## Complexity Assessment
**Track**: Simple Fix — single endpoint, no DB changes
