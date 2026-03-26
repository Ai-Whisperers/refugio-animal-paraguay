# RAP-002 Plan

## Objective
Create SQLAlchemy 2.x ORM models for animals, adopters, and adoption_requests that map to the schema defined in migration 001.

## Description
The Alembic migration (RAP-001) established the PostgreSQL schema. This ticket creates the Python ORM layer using SQLAlchemy 2.x declarative style. Models must match the schema exactly: UUID PKs, TIMESTAMPTZ columns, CHECK constraint enums, FK relationships, and Refugio naming conventions. These models are the foundation for all FastAPI service layers.

## Acceptance Criteria
- [ ] `Animal` model: all columns from migration (id, name, species, status, birth_date, description, created_at, updated_at)
- [ ] `Adopter` model: all columns (id, full_name, email, phone, address, gdpr_consent_at, deleted_at, created_at, updated_at)
- [ ] `AdoptionRequest` model: all columns (id, animal_id, adopter_id, status, submitted_at, decided_at, notes, created_at, updated_at)
- [ ] FK relationships: `AdoptionRequest.animal` → `Animal`, `AdoptionRequest.adopter` → `Adopter` (with back-populates)
- [ ] `AnimalStatus` and `AdoptionRequestStatus` Python enums matching CHECK constraint values
- [ ] `Base` declarative base in `src/db/base.py` — imported by all models
- [ ] `updated_at` auto-updates on every save via `onupdate=func.now()`
- [ ] Unit tests: model instantiation, relationship navigation, enum values match migration constraints
- [ ] All models importable from `src/db/models/__init__.py`

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria
- [ ] Single, clear root cause identified — N/A (new feature)
- [ ] ≤3 files affected — NO (5+ files: base.py, 3 model files, __init__.py, tests)
- [ ] ≤10 lines of code — NO (full model definitions)
- [ ] Low risk of side effects — YES
- [ ] Solution pattern is well-understood — YES

**Assessment**: Complex — multiple new files, model relationships, enum definitions, tests required.

## Approach
1. Create `src/db/base.py` — declarative base + shared column helpers
2. Create `src/db/models/animal.py` — `Animal` model + `AnimalStatus` enum
3. Create `src/db/models/adopter.py` — `Adopter` model
4. Create `src/db/models/adoption_request.py` — `AdoptionRequest` model + `AdoptionRequestStatus` enum
5. Create `src/db/models/__init__.py` — re-export all models
6. Create `tests/unit/test_models.py` — model instantiation and relationship tests

## Dependencies
- Depends on: RAP-001 (migration schema — defines column types and constraints)

## Risks
- Risk: SQLAlchemy 2.x mapped column syntax differs from 1.x → Mitigation: use `mapped_column()` and `Mapped[]` type annotations throughout (2.x style only)
- Risk: UUID handling varies by driver → Mitigation: use `sa.UUID(as_uuid=True)` consistent with migration
