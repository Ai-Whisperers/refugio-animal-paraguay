# RAP-005 Recap

## Outcome
Delivered Adopters CRUD API matching the plan exactly — all 5 endpoints, soft-delete, GDPR consent tracking, 409 on duplicate email.

## Acceptance Criteria — Final Status
- [x] `GET /adopters` — list excluding soft-deleted records
- [x] `GET /adopters/{id}` — 200 or 404 (404 if soft-deleted)
- [x] `POST /adopters` — create, 201; 409 if email already exists
- [x] `PATCH /adopters/{id}` — partial update including gdpr_consent grant
- [x] `DELETE /adopters/{id}` — soft delete (sets deleted_at), 204 or 404
- [x] Schemas: AdopterCreate, AdopterUpdate, AdopterResponse in `src/schemas/adopter.py`
- [x] Unit tests for schemas; integration tests for all endpoints
- [x] Zero Pyright errors

## Key Learnings
- `pydantic[email]` (email-validator) must be installed for `EmailStr`; it normalises the domain to lowercase but preserves the local part's case.
- Pydantic v2 error type names for length violations are `string_too_short` / `string_too_long`, not `min_length` / `max_length`.
- Using `_unique_email()` helper in integration tests avoids 409 collisions between tests that don't clean up their records.

## Follow-Up Actions
- [ ] RAP-006: Adoption requests workflow (POST, GET, PATCH status)

## Validation Evidence
- Unit tests: 13 passing, 0 failing (69 total unit suite)
- Integration tests: 19 passing, 0 failing (36 total integration suite)
- Pyright: 0 errors, 0 warnings
- Linting: clean
