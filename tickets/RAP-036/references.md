# RAP-036 References

## Key Files
- `src/db/models/donation.py` — Donation, Donor, PaymentMethod, CurrencyCode enums
- `src/api/donations.py` — Existing donation endpoints
- `src/api/webhooks.py` — Stripe webhook handler (RAP-034)
- `src/schemas/donation.py` — Donation schemas
- `src/config.py` — Stripe config settings
- `.claude/skills/payment-patterns.md` — SEPA patterns reference

## New Files (to create)
- `src/db/models/sepa_mandate.py` — SepaMandate model
- `src/services/sepa_service.py` — SEPA business logic
- `src/api/sepa.py` — SEPA API endpoints
- `src/schemas/sepa.py` — SEPA schemas
- `src/utils/iban.py` — IBAN validation/masking
- `src/db/alembic/versions/010_add_sepa_support.py` — Migration
