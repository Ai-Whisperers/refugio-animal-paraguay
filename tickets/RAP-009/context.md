# RAP-009 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26 00:30

## Current Focus
Ticket complete.

## Technical State
- `src/db/models/donation.py` — Donor + Donation ORM models with enums (CurrencyCode, PaymentMethod, DonationStatus)
- `src/db/models/__init__.py` — Exports all donation models
- `src/db/alembic/versions/004_add_donors_and_donations.py` — Migration: donors + donations tables with CHECK constraints, indexes, FK with SET NULL
- `src/schemas/donation.py` — DonorCreate, DonorResponse, DonationCreate, DonationResponse, StripeIntentResponse
- `src/api/donors.py` — POST /donors (public), GET /donors/{id} (staff only)
- `src/api/donations.py` — POST /donations (public), POST /donations/{id}/stripe-intent, GET /donations (staff), GET /donations/{id} (staff)
- `src/app.py` — Registered donors_router and donations_router
- `tests/integration/test_donations.py` — 26 integration tests covering all endpoints

## Key Decisions Made
- Amount stored as integer cents (not float) to avoid precision loss
- Anonymous donations: donor_id nullable FK with ondelete="SET NULL"
- PYG currency not supported by Stripe — returns 422 for stripe-intent attempts
- Stripe client_secret None guard → 502 (defensive; Stripe always returns it on create)
- GDPR consent tracked as nullable timestamp on Donor model
- Stripe PaymentIntent.create mocked in tests via unittest.mock.patch

## Next Steps
None — ticket complete.

## Blockers
None
