# RAP-012 Plan

## Objective
Implement structured animal intake workflow API capturing source, finder info, location, condition, and photos.

## Description
Staff members need to process new animals entering the shelter through a structured intake form. The intake record tracks how the animal arrived (stray, surrender, rescue, transfer), who found it, where it was found, its condition on arrival, and whether it needs quarantine. This supports impact reporting, medical triaging, and inventory management.

## Acceptance Criteria
- [x] Intake form with source categorization (stray, surrender, rescue, transfer) and finder info
- [x] Stray animals: location found, finder contact info, condition on arrival
- [x] Photos linked to animal record for impact reports
- [x] Quarantine flag triggers automatic medical record creation (stub for EPIC-4)
- [x] Animal added with status "intake" on submit

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified
- [x] Solution affects <=3 files — NO, affects 6+ files
- [ ] Change impact <=10 lines of actual code
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — New model, migration, schemas, API endpoints, and tests across multiple files.

## Approach
1. Create IntakeRecord SQLAlchemy model with IntakeSource enum
2. Write Alembic migration for intake_records table
3. Create Pydantic schemas for intake create/response
4. Build API endpoints (POST /animals/intake, GET /animals/intake, GET /animals/intake/{id})
5. Add quarantine stub logic (log + placeholder for EPIC-4 medical record creation)
6. Write unit tests for schemas and quarantine logic
7. Write integration tests for all endpoints

## Dependencies
- Depends on: EPIC-10 (Auth — already complete), EPIC-1 S01-S04 (Animal model — already complete)
- Links to: EPIC-4 (Medical records — stub only for now)

## Risks
- Risk: IntakeSource enum values might need expansion later -> Mitigation: Use string-backed enum, easy to add values via migration
- Risk: Medical record creation is a stub -> Mitigation: Log quarantine flag, create TODO for EPIC-4 integration
