# RAP-004 Plan

## Objective
Implement a complete Animals CRUD REST API (`GET /animals`, `GET /animals/{id}`, `POST /animals`, `PATCH /animals/{id}`, `DELETE /animals/{id}`) with Pydantic request/response schemas and unit + integration tests.

## Description
The Animal ORM model and migration exist from RAP-001/002. This ticket wires the model to a FastAPI router with proper schema validation, error handling (404, 422), and pagination for the list endpoint. This is the first domain API surface — its patterns become the template for Adopters (RAP-005) and Adoption Requests (RAP-006).

## Acceptance Criteria
- [ ] `GET /animals` — paginated list, filterable by `species` and `status`
- [ ] `GET /animals/{id}` — single animal or 404
- [ ] `POST /animals` — create animal, returns 201
- [ ] `PATCH /animals/{id}` — partial update (only provided fields changed), returns 200 or 404
- [ ] `DELETE /animals/{id}` — soft delete not in scope; hard delete, returns 204 or 404
- [ ] Pydantic schemas: `AnimalCreate`, `AnimalUpdate`, `AnimalResponse` in `src/schemas/animal.py`
- [ ] Router registered in `src/app.py`
- [ ] Unit tests for schema validation (field types, required vs optional)
- [ ] Integration tests for all 5 endpoints (happy path + 404 cases)
- [ ] Zero Pyright errors/warnings

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria
- [ ] Single, clear root cause identified — N/A (new feature)
- [ ] Solution affects ≤3 files — No: schemas, router, app, tests (5+ files)
- [ ] Change impact ≤10 lines — No: full CRUD implementation
- [ ] Low risk of side effects — Yes
- [ ] Solution pattern is well-understood — Yes (standard FastAPI CRUD)

**Assessment**: Complex — multi-file feature spanning schemas, router, app wiring, and two test layers.

## Approach

**Phase 1**: Schemas (`src/schemas/animal.py`) + unit tests
**Phase 2**: Router (`src/api/animals.py`) with all 5 endpoints
**Phase 3**: Register router in app, integration tests
**Phase 4**: Pyright clean, full test run

## Dependencies
- Depends on: RAP-003 (FastAPI app + session factory — complete)
- Depends on: RAP-001/002 (Animal model + migration — complete)

## Risks
- `onupdate=sa.func.now()` on `updated_at` only fires on ORM flush — Mitigation: use explicit `updated_at = datetime.now(UTC)` on PATCH to ensure it updates
- UUID primary key — Mitigation: use `uuid.UUID` type in path params, FastAPI validates automatically
