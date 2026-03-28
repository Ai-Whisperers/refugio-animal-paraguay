# RAP-640 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-28 11:27

## Current Focus

Ticket closed. All work committed on feature/RAP-640-volunteer-registration-form. PR #301 open.

## Technical State

- VolunteerProfile ORM model: `src/db/models/volunteer_profile.py`
- Migration 071: `src/db/alembic/versions/071_create_volunteer_profiles_table.py`
- API routers: `src/api/volunteer.py` (public + staff)
- Frontend form: `frontend/src/app/volunteer/apply/page.tsx`
- Unit tests: `tests/unit/test_volunteer.py` (25 tests)

## Next Steps

N/A — ticket complete. Awaiting PR #301 merge to develop.

## Blockers

None.

## Key Decisions Made

- Used RAP-640 instead of RAP-175 (ticket ID collision with UX sprint)
- Used `MagicMock(spec=VolunteerProfile)` in unit tests (SQLAlchemy mapper constraint)
- Skills and availability stored as JSON arrays (mirrors rescuer_profile.py pattern)
- Re-application allowed for rejected/inactive status (idempotent for pending/approved)
