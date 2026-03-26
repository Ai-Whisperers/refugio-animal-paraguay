# RAP-026 Plan

## Objective
Enable staff to record non-cash donations (food, supplies, vet services) with estimated values for impact reporting.

## Description
The shelter receives in-kind donations that need tracking separately from cash. These have an item type, quantity, estimated monetary value, and optional donor linkage. This data feeds into impact reports showing total donor contributions (cash + in-kind).

## Acceptance Criteria
- [ ] InKindDonation model with ItemType enum (food, medication, equipment, etc.)
- [ ] Alembic migration creating in_kind_donations table
- [ ] Pydantic schemas for create, update, and response
- [ ] Staff-only CRUD endpoints: POST, GET list (paginated), GET single
- [ ] Estimated value stored as integer cents (same pattern as cash donations)
- [ ] Links to existing donor records (optional — anonymous in-kind supported)
- [ ] Unit tests for model, schemas, and endpoint logic
- [ ] Ruff clean, all tests pass

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new model, migration, schema, API file, multiple endpoints, 5+ files

## Approach
1. Create InKindDonation model with ItemType enum
2. Alembic migration (007)
3. Pydantic schemas
4. API router with CRUD endpoints
5. Wire router into app.py
6. Unit tests
7. Quality gates

## Dependencies
- Depends on: RAP-009 (Donor model exists)
- No blockers

## Risks
- Risk: estimated_value precision → Mitigation: integer cents pattern (same as Donation)
