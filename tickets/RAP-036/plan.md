# RAP-036 Plan

## Objective
Add SEPA Direct Debit support for recurring EUR donations from EU donors via Stripe.

## Description
EU donors (primarily Dutch/German) need to set up recurring donations using SEPA Direct Debit, the standard EU bank transfer mechanism. This integrates with Stripe's SEPA payment method, creating SetupIntents for mandate collection and handling the asynchronous payment lifecycle via webhooks. SEPA payments take 5-14 business days to settle, so the async webhook flow is critical.

## Acceptance Criteria
- [ ] PaymentMethod enum extended with "sepa_debit" value
- [ ] New SepaMandate model tracking mandate status per donor
- [ ] Alembic migration for sepa_mandates table + payment_method CHECK update
- [ ] SEPA service: create SetupIntent, confirm mandate, create subscription
- [ ] API endpoints: POST /donations/sepa-setup (create mandate), GET /donors/{id}/mandates
- [ ] Webhook handlers for SEPA-specific events (setup_intent.succeeded, charge.succeeded for SEPA)
- [ ] IBAN validation utility
- [ ] Unit tests for service layer
- [ ] Integration tests for API endpoints
- [ ] IBAN masking for logs (never log full IBAN)

## Complexity Assessment
**Track**: Complex Implementation

### Assessment
- Multiple files affected (model, migration, service, API, schemas, webhooks, tests)
- Async payment lifecycle with multiple Stripe event types
- IBAN validation and masking requirements
- Mandate lifecycle management (pending -> active -> revoked)

## Approach
1. Extend PaymentMethod enum, create SepaMandate model + migration
2. Add IBAN validation utility
3. Create SEPA service (SetupIntent creation, mandate management)
4. Add API endpoints
5. Extend webhook handler for SEPA events
6. Write schemas
7. Write tests

## Dependencies
- Depends on: RAP-034 (Stripe Webhooks) — DONE (PR #25)
- Stripe SDK v15 with SEPA support

## Risks
- Risk: SEPA settlement delay (5-14 days) means donation status stays pending longer → Mitigation: Clear status messaging, webhook-driven updates
- Risk: IBAN validation complexity → Mitigation: Use basic format validation, recommend python-stdnum for production
