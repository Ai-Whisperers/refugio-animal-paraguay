# RAP-002 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-25 23:20

## Current Focus
Create SQLAlchemy 2.x ORM models mapping to the schema from RAP-001 migration.

## Technical State
- SQLAlchemy 2.x declarative style: `DeclarativeBase`, `Mapped[T]`, `mapped_column()`
- Migration schema source: `src/db/migrations/001_create_core_animal_adoption_tables.py`
- UUID PKs: `sa.UUID(as_uuid=True)` with `server_default=func.gen_random_uuid()`
- Timestamps: `TIMESTAMP(timezone=True)` — all timezone-aware
- Status values: VARCHAR with CHECK constraints → Python `enum.Enum` classes
- Target structure: `src/db/base.py`, `src/db/models/{animal,adopter,adoption_request}.py`

## Next Steps
1. Create `src/db/base.py` with `DeclarativeBase` subclass
2. Create `Animal` model with `AnimalStatus` enum
3. Create `Adopter` model
4. Create `AdoptionRequest` model with FK relationships
5. Wire `src/db/models/__init__.py`
6. Write unit tests

## Blockers
None

## Key Decisions Made
None yet
