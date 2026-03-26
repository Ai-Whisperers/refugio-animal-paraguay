# RAP-005 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-25

## Current Focus
Ticket closed.

## Technical State
- `src/schemas/adopter.py` — AdopterCreate, AdopterUpdate, AdopterResponse
- `src/api/adopters.py` — full CRUD router, soft-delete, GDPR consent, 409 on email conflict
- `src/app.py` — adopters_router registered
- `tests/unit/test_adopter_schemas.py` — 13 unit tests
- `tests/integration/test_adopters.py` — 19 integration tests

## Blockers
None

## Key Decisions Made
- Soft delete via `deleted_at` timestamp — preserves GDPR audit trail and FK refs from adoption_requests
- `pydantic[email]` required for EmailStr; added via pip
- Email domain normalised to lowercase by Pydantic; local part preserved
