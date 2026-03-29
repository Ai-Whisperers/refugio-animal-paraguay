# RAP-245 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:00

## Current Focus
Implementing SENACSA registration number tracking on the Animal model.

## Technical State
- Migration: will be 090_add_senacsa_registration_number_to_animals.py
- Model: src/db/models/animal.py — add `senacsa_registration_number: Mapped[str | None]`
- Schema: src/schemas/animal.py — add field to Create/Update/Response
- Router: src/api/animals.py — accept in create/update, filter on list
- Tests: tests/unit/test_senacsa_registration.py, tests/integration/test_senacsa_registration.py

## Next Steps
1. Write migration
2. Update model
3. Update schemas
4. Update router
5. Write tests

## Blockers
None

## Key Decisions Made
- Field is nullable (not all animals may have a SENACSA number yet)
- Field is a free-form string (SENACSA numbers are alphanumeric, no fixed format enforced at DB level)
- Add `senacsa_registered` boolean query param to GET /animals for convenient filtering
