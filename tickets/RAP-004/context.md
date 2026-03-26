# RAP-004 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-25

## Current Focus
Phase 1 — Pydantic schemas for Animal.

## Technical State
- Animal ORM model: `src/db/models/animal.py` (AnimalSpecies, AnimalStatus enums + Animal model)
- FastAPI app + async session: `src/app.py`, `src/db/session.py`
- No schemas dir yet; no animals router

## Next Steps
1. Create `src/schemas/__init__.py` and `src/schemas/animal.py`
2. Unit tests for schemas
3. Create `src/api/animals.py` router
4. Integration tests
5. Register router in app.py

## Blockers
None

## Key Decisions Made
- Use `UUID` path params (FastAPI validates automatically)
- Pagination via `?offset=0&limit=20` query params (simple, no cursor needed at this stage)
- PATCH accepts partial update — all fields Optional in AnimalUpdate
- Hard delete for now (soft delete deferred)
