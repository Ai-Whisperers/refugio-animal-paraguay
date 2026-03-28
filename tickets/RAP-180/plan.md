# RAP-180 Plan

## Objective
Implement a Shift model with time slots and capacity tracking for the shelter volunteer scheduling system.

## Description
Volunteers need to sign up for specific shifts at the shelter. This story creates the database model, API endpoints, and Pydantic schemas so staff can create and manage shifts (date, start/end time, capacity, role type).

## Acceptance Criteria
- [ ] `Shift` SQLAlchemy model with: date, start_time, end_time, capacity, slots_filled, role, status, notes
- [ ] `ShiftSignup` model to track which volunteers are assigned to which shifts
- [ ] API endpoints: POST /api/shifts (create), GET /api/shifts (list with filters), GET /api/shifts/{id} (detail), PATCH /api/shifts/{id} (update), DELETE /api/shifts/{id} (staff only)
- [ ] Input validation via Pydantic v2 schemas
- [ ] Unit tests for schema validation (80%+ coverage)
- [ ] Integration tests for CRUD endpoints
- [ ] OpenAPI schema populated

## Complexity Assessment
**Track**: Complex Implementation

### Complex Criteria
- New DB model + migration + API + tests across multiple files
- FK relation between Shift and User/VolunteerProfile

**Assessment result**: Complex — new model, migration, API router, schemas, tests

## Approach
1. Create `src/db/models/shift.py` with Shift + ShiftSignup models
2. Create `src/api/shifts.py` with CRUD endpoints
3. Register router in `src/app.py`
4. Write unit tests and integration tests

## Dependencies
- Depends on: volunteer_profile model (done)
- Blocked by: None

## Risks
- Risk: Migration drift if DB not available → Mitigation: Use SQLAlchemy model only (no alembic migration needed for dev)
