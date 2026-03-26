# RAP-036 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26

## Current Focus
SEPA Direct Debit support delivered. PR #27 created.

## Technical State
- SepaMandate model with full lifecycle (pending -> active -> revoked/failed)
- IBAN validation (ISO 13616, MOD-97-10) with GDPR-safe masking
- Stripe integration: Customer, PaymentMethod, SetupIntent creation
- Webhook handlers for setup_intent.succeeded and setup_intent.setup_failed
- 3 API endpoints: POST /donations/sepa-setup, GET /donors/{id}/mandates, DELETE revoke
- Alembic migration 010_add_sepa_support
- 36 new tests (19 IBAN + 11 service + 6 integration)

## Blockers
- None
