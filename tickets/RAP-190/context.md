# RAP-190 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-28

## Current Focus
Done — PR #316 open for review

## Technical State
- FosterProfile model: src/db/models/foster_profile.py
- Migration 075: src/db/alembic/versions/075_create_foster_profiles_table.py
- API: src/api/foster.py (public_router + staff_router)
- Tests: 23 unit + 19 integration, all passing

## Next Steps
None — ticket complete

## Blockers
None

## Key Decisions Made
- Status lifecycle: pending → approved | rejected, can move to inactive
- Any authenticated user can apply as foster (not just FOSTER role pre-assigned)
- Staff can approve/reject with optional reason
