# RAP-006 Plan

## Objective
Implement Adoption Requests workflow API — create, list, get, and update status with business-rule enforcement.

## Acceptance Criteria
- [x] `POST /adoption-requests` — create, 201; 404 if animal or adopter not found
- [x] `GET /adoption-requests` — paginated list; optional filter by status, animal_id, adopter_id
- [x] `GET /adoption-requests/{id}` — single request or 404
- [x] `PATCH /adoption-requests/{id}/status` — update status with transitions; approved sets animal status → adopted; only PENDING can be approved/rejected; any non-cancelled can be cancelled
- [x] Schemas: AdoptionRequestCreate, AdoptionRequestStatusUpdate, AdoptionRequestResponse
- [x] Unit tests for schemas; integration tests for all endpoints
- [x] Zero Pyright errors

## Complexity Assessment
**Track**: Complex — multi-entity FK validation, business-rule status transitions, cross-model side effects (animal status update on approval)

## Approach
Phase 1: schemas → Phase 2: router + business rules → Phase 3: register + tests
