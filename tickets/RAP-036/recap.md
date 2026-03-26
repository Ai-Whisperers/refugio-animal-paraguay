# RAP-036 Recap

## Outcome
Delivered SEPA Direct Debit payment method and recurring donation subscription support, matching all acceptance criteria from the EPIC-3 S02 story.

## What Was Delivered
- SEPA Direct Debit as a new payment method for EUR donations
- Stripe PaymentIntent creation with `payment_method_types=["sepa_debit"]`
- Recurring subscription creation (monthly/yearly via Stripe Subscriptions)
- Subscription cancellation endpoint
- Webhook handlers for invoice.payment_succeeded, invoice.payment_failed, customer.subscription.deleted
- Alembic migration 014 adding subscription columns and updating CHECK constraints
- 40 new tests (28 unit + 12 integration), all passing

## Acceptance Criteria — Final Status
- [x] SEPA Direct Debit available as payment method for EUR donations
- [x] Stripe PaymentIntent created with sepa_debit payment method type
- [x] Recurring donation subscriptions (monthly/annual)
- [x] Subscription lifecycle webhooks handled
- [x] Donation model extended with subscription tracking fields
- [x] Database migration for new columns and constraints
- [x] Idempotent webhook processing
- [x] Unit tests for all new logic
- [x] Integration tests for endpoints and webhooks

## Key Learnings
- Subscription queries must handle multiple donations per subscription ID (use order_by + limit(1))
- SEPA Direct Debit requires a Stripe Customer for mandate tracking — anonymous donations not supported
- Invoice events (for subscriptions) don't carry payment_intent_id directly — need separate dispatch path

## Validation Evidence
- Tests: 789 passing, 0 failing (40 new tests added)
- Linting: clean (no new warnings in modified files)
- Formatting: clean
- Coverage: maintained above 80%
