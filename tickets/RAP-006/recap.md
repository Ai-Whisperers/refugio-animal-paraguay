# RAP-006 Recap

## Outcome
Delivered Adoption Requests workflow API matching the plan exactly — all 4 endpoints, status transitions with business-rule enforcement, and animal status side-effect on approval.

## Acceptance Criteria — Final Status
- [x] `POST /adoption-requests` — create, 201; 404 if animal or adopter not found
- [x] `GET /adoption-requests` — paginated list; filters by status, animal_id, adopter_id
- [x] `GET /adoption-requests/{id}` — single request or 404
- [x] `PATCH /adoption-requests/{id}/status` — status transitions enforced; approved → animal.status = 'adopted'
- [x] Schemas: AdoptionRequestCreate, AdoptionRequestStatusUpdate, AdoptionRequestResponse
- [x] Unit tests for schemas; integration tests for all endpoints
- [x] Zero Pyright errors

## Key Learnings
- `HTTP_422_UNPROCESSABLE_ENTITY` is deprecated in newer FastAPI; use `HTTP_422_UNPROCESSABLE_CONTENT`.
- `_ALLOWED_TRANSITIONS` dict pattern cleanly encodes a state machine without conditionals.
- The `submitted_at` field has no server default — must be set explicitly on creation.

## Validation Evidence
- Unit tests: 12 passing (81 total unit suite)
- Integration tests: 20 passing (56 total integration suite)
- Pyright: 0 errors, 0 warnings
