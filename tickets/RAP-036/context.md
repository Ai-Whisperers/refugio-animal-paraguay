# RAP-036 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Implementing SEPA Direct Debit and recurring donation subscription support.

## Technical State
- Existing Stripe PaymentIntent flow in src/api/donations.py
- Existing webhook handler in src/api/webhooks.py handles payment_intent.succeeded/failed and charge.refunded
- Donation model has stripe_payment_intent_id but no subscription fields
- DB CHECK constraint limits payment_method to ('stripe', 'cash', 'transfer')

## Next Steps
1. Create migration for new columns and constraint update
2. Update model enums and ORM
3. Implement SEPA and subscription endpoints
4. Extend webhook handler
5. Write tests

## Blockers
- None

## Key Decisions Made
- Using Stripe's native SEPA support (not standalone SEPA API)
- Storing stripe_subscription_id and stripe_customer_id on donations table
- Adding is_recurring boolean flag for query filtering
