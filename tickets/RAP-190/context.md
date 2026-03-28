# RAP-190 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-28

## Current Focus
Implementing FosterProfile model, migration, and API endpoints

## Technical State
- User model already has FOSTER role (UserRole.FOSTER = "foster")
- Volunteer registration pattern at src/db/models/volunteer_profile.py + src/api/volunteer.py
- Last alembic migration: 074_create_tasks_table.py (down_revision = "073")
- App registers routers in src/app.py around line 480

## Next Steps
1. Create FosterProfile model
2. Create migration 075
3. Create foster API
4. Register in app.py
5. Write tests

## Blockers
None

## Key Decisions Made
- Status lifecycle: pending → approved | rejected, can move to inactive
- Any authenticated user can apply as foster (not just FOSTER role pre-assigned)
- Staff can approve/reject with optional reason
