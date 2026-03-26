# RAP-037 Recap

## Outcome
Delivered animal sponsorship tiers (Bronze $10, Silver $25, Gold $50) with recurring Stripe Subscriptions. Backend only — frontend deferred.

## Acceptance Criteria — Final Status
- [x] Sponsorship model with tier enum and lifecycle states
- [x] Alembic migration with partial unique index for active sponsorships
- [x] Stripe Subscription integration (create, pause, resume, cancel, tier change)
- [x] POST /sponsorships endpoint (201)
- [x] GET /donors/{id}/sponsorships endpoint
- [x] GET /animals/{id}/sponsors endpoint
- [x] PATCH /sponsorships/{id} (tier change, pause, resume)
- [x] DELETE /sponsorships/{id} (cancel)
- [x] Webhook handling for subscription lifecycle events
- [x] Unit and integration tests

## Key Learnings
- Stripe Price.create requires `cast(Any, ...)` for `recurring` param due to Literal type mismatch
- ruff prefers `datetime.UTC` over `timezone.utc` (UP017)
- Partial unique indexes work well for "one active per pair" constraints

## Validation Evidence
- Tests: 354 unit passing, 0 failing
- Ruff: clean
- Pyright: 0 errors
- Bandit: clean
- Black: all files formatted
