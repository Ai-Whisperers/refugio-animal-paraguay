# RAP-142 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-27 00:00

## Current Focus
Implementing surgery scheduling interface — backend endpoint + frontend page.

## Technical State
- Surgery model in `src/db/models/surgery.py` — has Surgery + PostOpCheck tables
- Surgery API in `src/api/surgeries.py` — has per-animal list, no global list
- Need: `GET /surgeries` returning all surgeries with animal name
- Frontend: Follow vaccinations page pattern

## Next Steps
1. Add `SurgeryWithAnimalName` schema to `src/schemas/surgery.py`
2. Add `GET /surgeries` endpoint to `src/api/surgeries.py`
3. Add frontend types to `frontend/src/types/api.ts`
4. Create `frontend/src/app/admin/surgeries/page.tsx`
5. Update AdminSidebar with surgery link
6. Write tests

## Blockers
None.

## Key Decisions Made
- Using animal JOIN to include name in surgery list response
- Frontend follows vaccinations page pattern with status filter sections
