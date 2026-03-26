# RAP-034 References

## Key Files
- src/api/donations.py — Existing donation endpoints, Stripe PaymentIntent creation
- src/db/models/donation.py — Donation model with status, stripe_payment_intent_id
- src/schemas/donation.py — Donation Pydantic schemas
- src/events/domain_events.py — DonationReceived event and factory
- src/events/bus.py — EventBus implementation
- src/events/types.py — EventType enum (DONATION_RECEIVED, DONATION_REFUNDED)
- src/config.py — Settings (needs STRIPE_WEBHOOK_SECRET)
- src/app.py — App factory (needs webhook router registration)

## New Files
- src/api/webhooks.py — Stripe webhook endpoint
- tests/unit/test_webhooks.py — Unit tests
- tests/integration/test_webhooks.py — Integration tests
