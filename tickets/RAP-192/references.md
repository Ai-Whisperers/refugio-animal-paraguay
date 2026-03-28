# RAP-192 References

## Key Files
- `src/db/models/foster_profile.py` — FosterProfile model
- `src/db/models/foster_placement.py` — FosterPlacement model
- `src/api/foster.py` — Foster router (public + staff endpoints)
- `src/services/foster_placement_service.py` — Placement service
- `src/db/alembic/versions/076_create_foster_placements_table.py` — Latest migration

## New Files Created
- `src/db/models/foster_check_in.py` — FosterCheckIn model
- `src/db/alembic/versions/077_create_foster_check_ins_table.py` — Migration
- `src/services/foster_check_in_service.py` — Check-in service
- `tests/unit/test_foster_check_in_service.py` — Unit tests
- `tests/integration/test_foster_check_in.py` — Integration tests
