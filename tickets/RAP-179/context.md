# RAP-179 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-28 17:40

## Current Focus
Creating volunteer directory page for staff at /admin/volunteers/directory.

## Technical State
- Backend API exists: GET /api/staff/volunteers?status=approved (paginated, staff-only)
- Existing page: /admin/volunteers shows application review queue (all statuses)
- VolunteerListItem type already in frontend/src/types/api.ts
- Pattern: follows AdminDonors.test.tsx, AdminDonorsPage patterns

## Next Steps
1. Create frontend/src/app/admin/volunteers/directory/page.tsx
2. Create frontend/tests/components/VolunteerDirectory.test.tsx
3. Run vitest, check passes

## Blockers
- none

## Key Decisions Made
- Client-side filtering by skill/availability (data already in API response)
- Large page_size=100 to load all approved volunteers for directory use
- Separate route (/directory) from application review (/volunteers) to keep concerns distinct
