# RAP-036 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Implementing SEPA Direct Debit support for EU recurring donations.

## Technical State
- Stripe SDK v15 integrated, webhook handler exists (RAP-034)
- Donation model has amount_cents, currency, payment_method, stripe_payment_intent_id
- PaymentMethod enum: stripe, cash, transfer (needs sepa_debit)
- Webhook handler processes payment_intent.succeeded/failed, charge.refunded

## Next Steps
1. Extend PaymentMethod enum with sepa_debit
2. Create SepaMandate model + migration
3. Add IBAN validation utility
4. Create SEPA service
5. Add API endpoints and schemas
6. Extend webhook handler for SEPA events
7. Write tests

## Blockers
- None
