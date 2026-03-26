# RAP-004 Recap

## Outcome
Full Animals CRUD API delivered — all 5 endpoints live, schemas validated, 72 tests passing.

## Acceptance Criteria — Final Status
- [x] `GET /animals` — paginated list with species/status filters
- [x] `GET /animals/{id}` — 200 or 404
- [x] `POST /animals` — 201 Created
- [x] `PATCH /animals/{id}` — partial update, 200 or 404
- [x] `DELETE /animals/{id}` — hard delete, 204 or 404
- [x] Schemas: AnimalCreate, AnimalUpdate, AnimalResponse in `src/schemas/animal.py`
- [x] Router registered in `src/app.py`
- [x] Unit tests for schema validation (18 tests)
- [x] Integration tests for all 5 endpoints (16 tests)
- [x] Zero Pyright errors/warnings

## Key Learnings
- Pydantic v2 uses `string_too_short`/`string_too_long` error types (not `min_length`/`max_length`) — match strings in test assertions must use the type, not the parameter name.
- `model_dump(exclude_unset=True)` is the correct way to implement partial PATCH — only fields explicitly provided in the request body are included.
- Setting `updated_at = datetime.now(UTC)` explicitly on PATCH ensures the value is visible after `refresh()` (SQLAlchemy's `onupdate` hook fires at flush but the local attribute may not reflect it until re-fetched).

## Validation Evidence
- Tests: 72 passing, 0 failing
- Pyright: 0 errors, 0 warnings, 0 informations
