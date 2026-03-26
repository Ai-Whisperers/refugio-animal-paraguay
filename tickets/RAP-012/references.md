# RAP-012 References

## Key Files
- src/db/models/intake.py (NEW)
- src/schemas/intake.py (NEW)
- src/api/intake.py (NEW)
- src/db/alembic/versions/005_add_intake_records.py (NEW)
- src/db/models/__init__.py (MODIFIED)
- src/app.py (MODIFIED)
- tests/unit/test_intake_schemas.py (NEW)
- tests/integration/test_intake.py (NEW)

## Story
- planning/epics/EPIC-1-animal-catalog-and-management/stories/S06-animal-intake-workflow/STORY.md

## Existing Patterns
- src/db/models/animal.py — model pattern
- src/api/animals.py — router pattern
- src/schemas/animal.py — schema pattern
- src/auth/dependencies.py — require_staff dependency
