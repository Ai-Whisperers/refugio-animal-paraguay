# RAP-640 Plan

## Objective

Implement the volunteer registration form (public-facing) and the backend model, API, and migration for EPIC-36 S1.

## Description

Volunteers are a core operational resource for Refugio Animal Paraguay. This ticket delivers the data model, REST API, and application form required for volunteers to apply, and for staff to review applications.

## Acceptance Criteria

- [x] POST /api/volunteers/apply creates a VolunteerProfile for the authenticated user
- [x] GET /api/volunteers/me returns the current user's volunteer profile
- [x] PUT /api/volunteers/me allows self-editing when status is pending or inactive
- [x] GET /api/staff/volunteers lists applications with pagination and optional status filter
- [x] PUT /api/staff/volunteers/{id}/review approves or rejects a pending application
- [x] Rejected applications require a rejection_reason (422 otherwise)
- [x] Re-application allowed after rejection/inactive (409 for pending/approved)
- [x] VolunteerProfile model with motivation (min 20 chars), skills, availability, hours_per_week (1-40)
- [x] Alembic migration 071 with CHECK constraints and status/user_id indexes
- [x] Unit tests: schemas, validation, and response builder

## Complexity Assessment

**Track**: Complex Implementation

**Assessment result**: Complex — fullstack (model, migration, 4 API endpoints, frontend form, 25 tests), >3 files, multiple layers.

## Approach

1. ORM model and migration (foundation)
2. FastAPI routers (public apply/me + staff list/review)
3. Register routers in app.py
4. Next.js application form (frontend)
5. Unit tests
6. Quality gates and PR

## Dependencies

- Depends on: `src/db/models/user.py` (User FK), `src/auth/dependencies.py` (get_current_user, require_staff)
- Blocked by: None

## Risks

- Ticket ID collision (RAP-175 already used) → Used RAP-640
- SQLAlchemy ORM `__new__` issue in unit tests → Used MagicMock(spec=Model) instead>>>>>>> 550e560 (RAP-640: Add volunteer registration form, profile model, API, and staff review)
