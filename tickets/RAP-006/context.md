# RAP-006 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-25

## Technical State
- `src/schemas/adoption_request.py` — AdoptionRequestCreate, AdoptionRequestStatusUpdate, AdoptionRequestResponse
- `src/api/adoption_requests.py` — full workflow router, status transitions, animal side-effect
- `src/app.py` — adoption_requests_router registered
- `tests/unit/test_adoption_request_schemas.py` — 12 unit tests
- `tests/integration/test_adoption_requests.py` — 20 integration tests

## Key Decisions Made
- Status transition table (dict mapping current → allowed next states) centralises all business rules
- Approval side-effect updates animal.status in the same flush — atomic
- `HTTP_422_UNPROCESSABLE_CONTENT` used (not deprecated `HTTP_422_UNPROCESSABLE_ENTITY`)
- `submitted_at` set explicitly with `datetime.now(UTC)` — no server default on the model
