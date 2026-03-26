# RAP-009 Recap

## Outcome
Donations API fully implemented: donor profiles, anonymous donations, Stripe PaymentIntent creation, staff-only list/get endpoints.

## Acceptance Criteria — Final Status
- [x] POST /donors — create donor profile (public, email unique)
- [x] GET /donors/{id} — staff only, 404 on missing
- [x] POST /donations — create donation (public, supports anonymous)
- [x] POST /donations/{id}/stripe-intent — create Stripe PaymentIntent, return client_secret
- [x] GET /donations — paginated list with currency/status filters (staff only)
- [x] GET /donations/{id} — single donation (staff only)
- [x] PYG not supported by Stripe → 422
- [x] Stripe key missing → 503
- [x] Migration 004 applied

## Key Learnings
- Stripe SDK v15 types `client_secret` as `str | None` even though create() always returns it — requires explicit None guard for Pyright
- Anonymous donations: donor_id = None + ondelete="SET NULL" FK covers the case where a donor is later deleted
- `patch.dict("os.environ", ...)` in tests correctly isolates env state for Stripe key tests

## Validation Evidence
- Tests: 204 passing (96 unit, 108 integration), 0 failing
- Pyright: 0 errors, 0 warnings
- Migration: applied cleanly (003 → 004)
