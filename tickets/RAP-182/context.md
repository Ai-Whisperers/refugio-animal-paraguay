# RAP-182 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-28 19:30

## Current Focus
Implementing volunteer self-signup for open shifts.

## Technical State
- ShiftSignup model already exists in src/db/models/shift.py
- No signup endpoints exist yet — adding to src/api/shifts.py
- Frontend: new page at frontend/src/app/volunteer/shifts/page.tsx

## Next Steps
1. Add POST/DELETE/GET endpoints to shifts.py
2. Wire into main.py
3. Add TypeScript types
4. Build frontend page
5. Write tests

## Blockers
None.

## Key Decisions Made
- Signup endpoints added to existing shifts.py (same file, keeps concerns together)
- Use DB-level atomic increment for slots_filled to avoid race conditions
