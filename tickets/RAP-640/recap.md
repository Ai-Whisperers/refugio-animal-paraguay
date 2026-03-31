# RAP-640 Recap

## Outcome

Delivered all planned components for EPIC-36 S1 (Volunteer registration form + backend model):

- `src/db/models/volunteer_profile.py` — VolunteerProfile ORM model with full lifecycle
- `src/db/alembic/versions/071_create_volunteer_profiles_table.py` — migration with CHECK constraints
- `src/api/volunteer.py` — 4 REST endpoints (public apply/me + staff list/review)
- `frontend/src/app/volunteer/apply/page.tsx` — Next.js application form
- `tests/unit/test_volunteer.py` — 25 unit tests, 100% passing

PR #301 open against develop.

## Acceptance Criteria — Final Status

- [x] Volunteer can submit an application (POST /api/volunteers/apply)
- [x] Volunteer can view their own profile (GET /api/volunteers/me)
- [x] Volunteer can update their profile when pending/inactive (PUT /api/volunteers/me)
- [x] Staff can list all applications with pagination and status filter
- [x] Staff can approve or reject applications with optional rejection reason
- [x] Re-application allowed after rejection or inactivity (idempotent for pending/approved)
- [x] VolunteerProfile model with 13 skill options, 6 availability slots, and status lifecycle
- [x] Alembic migration 071 with CHECK constraints and indexes
- [x] 25 unit tests pass, ruff clean, black clean

## Key Learnings

- SQLAlchemy ORM models cannot be instantiated via `__new__()` in unit tests without triggering the mapper instrumentation. Use `MagicMock(spec=Model)` instead.
- Ticket ID collision: EPIC-36 planning files assign RAP-175 to S1, but RAP-175 was used for "Homepage Redesign" in the UX sprint. Used RAP-640 (next available).

## Validation Evidence

- Tests: 25 passed, 0 failed (`pytest tests/unit/test_volunteer.py`)
- Linting: ruff clean
- Format: black clean
- No regressions in volunteer_driver tests (44/44 pass)
- Branch: feature/RAP-640-volunteer-registration-form
- PR: #301 (open, targets develop)
