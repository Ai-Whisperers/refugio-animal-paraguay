# RAP-195 Plan

## Objective
Implement volunteer hours logging and tracking — a fullstack feature allowing volunteers to log hours and staff to view/manage them.

## Description
Volunteers need a way to log hours worked outside of structured shifts (e.g., foster visits, independent tasks). Staff need to view aggregate hours per volunteer for recognition and reporting. This is the foundation for the leaderboard (RAP-196) and analytics (RAP-197).

## Acceptance Criteria
- [ ] VolunteerHoursLog ORM model created with Alembic migration
- [ ] API endpoints: POST /api/volunteers/hours (log hours), GET /api/volunteers/hours/me (own logs), GET /api/staff/volunteers/{id}/hours (staff view)
- [ ] Unit tests for schema validation
- [ ] Integration tests for API endpoints (happy path)
- [ ] ruff, black, pytest all pass

## Complexity Assessment
**Track**: Complex

### Assessment result: Complex — new model, migration, service logic, 3+ API endpoints, frontend page

## Approach
1. Create VolunteerHoursLog model (src/db/models/volunteer_hours.py)
2. Create Alembic migration 079
3. Create API endpoints in src/api/volunteer_hours.py
4. Register router in main app
5. Write unit tests and integration tests

## Dependencies
- Depends on: RAP-640 (volunteer_profiles), RAP-180 (shifts table)
- Blocked by: None

## Risks
- Alembic multi-head issue may affect migration: use raw SQL to apply in test
