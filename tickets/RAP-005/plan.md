# RAP-005 Plan

## Objective
Implement Adopters CRUD API with soft-delete and GDPR consent tracking.

## Acceptance Criteria
- [ ] `GET /adopters` — list excluding soft-deleted records
- [ ] `GET /adopters/{id}` — 200 or 404 (404 if soft-deleted)
- [ ] `POST /adopters` — create, 201; 409 if email already exists
- [ ] `PATCH /adopters/{id}` — partial update including gdpr_consent grant
- [ ] `DELETE /adopters/{id}` — soft delete (sets deleted_at), 204 or 404
- [ ] Schemas: AdopterCreate, AdopterUpdate, AdopterResponse in `src/schemas/adopter.py`
- [ ] Unit tests for schemas; integration tests for all endpoints
- [ ] Zero Pyright errors

## Complexity Assessment
**Track**: Complex — multi-file, soft-delete logic, GDPR consent, email uniqueness

## Approach
Phase 1: schemas → Phase 2: router → Phase 3: register + tests
