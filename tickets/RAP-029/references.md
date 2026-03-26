# RAP-029 References

## Files Changed
- `src/api/public.py` — New public browsing router
- `src/schemas/public.py` — New public response schemas
- `src/db/alembic/versions/008_add_breed_size_gender_to_animals.py` — Migration
- `src/db/models/animal.py` — Added AnimalSize, AnimalGender enums + model fields
- `src/db/models/__init__.py` — Export new enums
- `src/schemas/animal.py` — Added breed/size/gender to Create/Update/Response schemas
- `src/api/animals.py` — Updated create/update handlers for new fields
- `src/app.py` — Registered public router

## Files Created (Tests)
- `tests/unit/test_public_schemas.py` — 11 unit tests
- `tests/integration/test_public_browsing.py` — 23 integration tests

## Files Modified (Existing Tests)
- `tests/unit/test_animal_schemas.py` — Updated _FakeAnimal for new fields
