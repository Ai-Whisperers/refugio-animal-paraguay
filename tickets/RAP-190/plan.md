# RAP-190 Plan

## Objective
Implement foster family registration and approval — allowing users to apply as foster families and staff to review/approve applications.

## Description
Foster families temporarily care for animals at home. This story adds the FosterProfile model, migration, application API (submit, view own profile), and staff review endpoints (list all, approve/reject). Follows the same pattern as volunteer registration (RAP-640/641).

## Acceptance Criteria
- [ ] FosterProfile ORM model with: motivation, home_type, outdoor_space, has_other_pets, max_animals, preferred_animal_types, experience_description, status, rejection_reason, reviewed_by, reviewed_at
- [ ] Alembic migration 075_create_foster_profiles_table.py
- [ ] POST /api/foster/apply — submit application (authenticated user with FOSTER role or any logged-in user)
- [ ] GET /api/foster/me — get own foster profile (authenticated)
- [ ] GET /api/staff/foster — list all applications with pagination (staff only)
- [ ] PUT /api/staff/foster/{id}/review — approve/reject with optional rejection reason (staff only)
- [ ] Unit tests: schema validation, enum correctness
- [ ] Integration tests: apply, get own, list, review flows
- [ ] ruff, black, pytest all pass

## Complexity Assessment
**Track**: Complex Implementation — 5+ files (model, migration, API, service, tests), ~120 lines of actual code

**Assessment result**: Complex — multiple files but follows well-understood volunteer registration pattern

## Approach
1. Create `src/db/models/foster_profile.py`
2. Create `src/db/alembic/versions/075_create_foster_profiles_table.py`
3. Create `src/api/foster.py` (public + staff routers)
4. Register routers in `src/app.py`
5. Write `tests/unit/test_foster_schemas.py`
6. Write `tests/integration/test_foster.py`

## Dependencies
- Depends on: RAP-500 (public user registration) — DONE (PR #152)
- User model has FOSTER role already defined

## Risks
- Risk: alembic migration chain conflicts → Mitigation: use down_revision = "074" (last migration)
