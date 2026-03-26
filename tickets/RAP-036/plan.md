# RAP-036 Plan

## Objective
Implement SEPA Direct Debit as a payment method and recurring donation subscriptions via Stripe for EU bank account holders.

## Description
EU donors need the ability to pay via SEPA Direct Debit (bank transfer) and set up recurring monthly/annual donations. This builds on the existing Stripe PaymentIntent infrastructure (RAP-009, RAP-025) by adding SEPA-specific payment method types, Stripe subscription management, and webhook handlers for subscription lifecycle events.

## Acceptance Criteria
- [ ] SEPA Direct Debit available as a payment method for EUR donations
- [ ] Stripe PaymentIntent created with `payment_method_types=["sepa_debit"]` for SEPA donations
- [ ] Recurring donation subscriptions can be created (monthly/annual intervals)
- [ ] Subscription lifecycle webhooks handled: created, renewed, failed, cancelled
- [ ] Donation model extended with subscription tracking fields
- [ ] Database migration adds new columns and updates CHECK constraints
- [ ] Idempotent webhook processing for subscription events
- [ ] Unit tests for all new service logic
- [ ] Integration tests for SEPA endpoints and subscription webhooks

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A (new feature)
- [x] Solution affects ≤3 files — NO, affects 5+ files
- [ ] Change impact ≤10 lines of actual code — NO, substantial new code
- [ ] Low risk of side effects — moderate (payment infrastructure)
- [x] Solution pattern is well-understood — follows existing Stripe patterns

**Assessment result**: Complex — multi-file feature spanning model, schema, API, webhook, and migration layers

## Approach
1. Add Alembic migration: new columns on donations (stripe_subscription_id, stripe_customer_id, is_recurring, recurring_interval), update payment_method CHECK constraint to include 'sepa_debit'
2. Update ORM model and enums (PaymentMethod, add SEPA_DEBIT)
3. Add Pydantic schemas for SEPA intent creation and subscription management
4. Add API endpoint: POST /donations/{id}/sepa-intent (create SEPA PaymentIntent)
5. Add API endpoints: POST /donations/subscribe, DELETE /donations/subscriptions/{id}
6. Extend webhook handler for subscription events (invoice.payment_succeeded, customer.subscription.deleted, etc.)
7. Write unit + integration tests

## Dependencies
- Depends on: RAP-009 (Stripe foundation), RAP-025 (webhook processing)
- Blocked by: nothing

## Risks
- Risk: SEPA mandate compliance requirements → Mitigation: Stripe handles mandate storage; we only collect IBAN via Stripe Elements
- Risk: CHECK constraint update on live DB → Mitigation: additive change only (adding enum value)
