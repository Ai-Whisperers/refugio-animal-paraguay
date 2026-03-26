# RAP-009 Plan

## Objective
Implement a Donations API with donor records, one-time and recurring donation tracking, EUR and PYG currency support, and Stripe payment intent creation.

## Description
The Dutch owner's European donor network is critical revenue. This ticket adds the data model and API for donations — donor profiles (separate from adopters), donation records with currency and amount, and Stripe payment intent creation for card payments. Webhook processing and recurring billing are deferred to a follow-up ticket.

## Acceptance Criteria
- [ ] `donors` table: id, full_name, email (unique), country, currency_preference (`EUR`|`PYG`|`USD`), gdpr_consent_at, created_at, updated_at
- [ ] `donations` table: id, donor_id (FK nullable — anonymous allowed), amount_cents (int), currency, payment_method (`stripe`|`cash`|`transfer`), stripe_payment_intent_id (nullable), status (`pending`|`completed`|`failed`|`refunded`), notes, created_at, updated_at
- [ ] Alembic migration 004 creates both tables
- [ ] `POST /donors` — create donor profile
- [ ] `GET /donors/{id}` — get donor (staff only)
- [ ] `POST /donations` — create donation record (public; anonymous if no donor_id)
- [ ] `POST /donations/{id}/stripe-intent` — create Stripe PaymentIntent, return client_secret (staff or public)
- [ ] `GET /donations` — paginated list with currency/status filters (staff only)
- [ ] `GET /donations/{id}` — single donation (staff only)
- [ ] Schemas: DonorCreate, DonorResponse, DonationCreate, DonationResponse, StripeIntentResponse
- [ ] Unit tests for schemas
- [ ] Integration tests for all endpoints (Stripe calls mocked)
- [ ] Zero Pyright errors

## Complexity Assessment
**Track**: Complex — two new tables, Stripe integration, EUR/PYG currency handling, GDPR considerations for EU donors

## Approach
Phase 1: DB models + migrations
Phase 2: Schemas + donor router
Phase 3: Donations router + Stripe intent
Phase 4: Tests

## Dependencies
- Depends on: RAP-007 (auth, for staff-protected endpoints)

## Risks
- Risk: Stripe SDK not installed → Mitigation: add `stripe` to dependencies, mock in tests
- Risk: Amount stored as float → precision errors → Mitigation: always store as integer cents
