# RAP-150 Plan

## Objective
Add SEPA SetupIntent endpoints to allow donors to save their bank account as a mandate for future charges.

## Description
The existing SEPA code creates PaymentIntents (charge immediately). For recurring SEPA donations, Stripe recommends
a SetupIntent flow: first save the bank account (mandate), then charge later. This story adds:
1. POST /donations/sepa/setup-intent — creates a Stripe SetupIntent to save SEPA payment method
2. GET /donations/sepa/payment-methods/{customer_id} — lists saved SEPA payment methods for a donor

## Acceptance Criteria
- [ ] POST /donations/sepa/setup-intent creates SetupIntent and returns client_secret
- [ ] GET /donations/sepa/payment-methods/{customer_id} lists stored SEPA payment methods
- [ ] Donor must exist; customer is created/retrieved from Stripe
- [ ] Errors handled: donor not found, Stripe unavailable, invalid inputs
- [ ] API endpoints in OpenAPI schema
- [ ] Unit and integration tests at 80%+ coverage

## Complexity Assessment
**Track**: Complex — adds 2 new endpoints with Stripe API calls and tests

## Approach
1. Add SetupIntentCreate/SetupIntentResponse schemas in src/schemas/donation.py
2. Add POST /donations/sepa/setup-intent in src/api/sepa.py
3. Add GET /donations/sepa/payment-methods/{customer_id} in src/api/sepa.py
4. Write unit tests (schema validation) and integration tests (API endpoints)

## Dependencies
- Depends on: existing SEPA foundation (sepa.py, donation model)
