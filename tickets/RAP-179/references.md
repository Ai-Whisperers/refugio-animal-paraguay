# RAP-179 References

## Key Files
- `frontend/src/app/admin/volunteers/directory/page.tsx` — new page (to create)
- `frontend/tests/components/VolunteerDirectory.test.tsx` — tests (to create)
- `frontend/src/app/admin/volunteers/page.tsx` — existing application review page (pattern)
- `frontend/src/app/admin/volunteers/[id]/page.tsx` — existing detail page
- `frontend/src/types/api.ts` — VolunteerListItem, PaginatedVolunteerList types
- `src/api/volunteer.py` — backend API (existing)
- `src/db/models/volunteer_profile.py` — VolunteerProfile model

## API Endpoints Used
- `GET /api/staff/volunteers?status=approved&page_size=100` — fetch approved volunteers
