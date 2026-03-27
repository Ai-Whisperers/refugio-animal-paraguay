# RAP-034 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26

## Current Focus
Implementing Stripe webhook endpoint and event handlers.

## Technical State
- Donation model has status field (pending/completed/failed/refunded) and stripe_payment_intent_id
- Event bus infrastructure exists with DonationReceived domain event
- Email notification system is wired to event bus
- Stripe SDK already in dependencies (stripe>=8.0)

## Next Steps
1. Add webhook secret to config
2. Create webhook router with signature verification
3. Wire up event handlers for payment lifecycle
4. Register router in app.py
5. Write tests

## Blockers
- None

## Key Decisions Made
- Webhook endpoint at /webhooks/stripe (not under /api prefix — Stripe needs direct access)
- Signature verification required in all environments except test
- Idempotent by checking current donation status before update
