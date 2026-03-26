# RAP-037 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Implementing sponsorship model, service, API, and tests.

## Technical State
- Donor model exists with stripe-related fields
- Animal model exists with status tracking
- Stripe SDK v15 integrated, webhook handler exists
- SEPA mandate pattern established (similar lifecycle management)

## Next Steps
1. Create Sponsorship model + SponsorshipTier/SponsorshipStatus enums
2. Create Alembic migration
3. Build schemas, service, API
4. Extend webhooks for subscription events
5. Write tests

## Blockers
- None
