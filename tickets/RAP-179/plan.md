# RAP-179 Plan

## Objective
Create a searchable, filterable volunteer directory page for staff at /admin/volunteers/directory.

## Description
Staff need an operational directory of approved volunteers they can quickly browse to find people with specific skills or availability. This is distinct from the existing /admin/volunteers page (application review queue) — the directory is focused on finding active volunteers for coordination.

## Acceptance Criteria
- [ ] Volunteer directory page renders at /admin/volunteers/directory
- [ ] Shows only approved volunteers by default, with option to show inactive
- [ ] Search by name or email
- [ ] Filter by skill tag (single or multi)
- [ ] Filter by availability window
- [ ] Displays: name, email, skills, availability, hours/week, total hours logged
- [ ] Empty state handled (no approved volunteers, no search matches)
- [ ] Loading and error states present
- [ ] Links to individual volunteer detail page
- [ ] Unit tests passing (Vitest, 80%+ coverage on component logic)

## Complexity Assessment
**Track**: Simple Fix — single frontend page, uses existing API endpoint (GET /api/staff/volunteers?status=approved), no backend changes needed.

**Assessment result**: Simple Fix — one new .tsx file, one test file, no schema changes.

## Approach
1. New page: frontend/src/app/admin/volunteers/directory/page.tsx
2. Uses existing GET /api/staff/volunteers?status=approved&page=N API
3. Client-side search/filter for skill and availability (data already in response)
4. Test file: frontend/tests/components/VolunteerDirectory.test.tsx

## Dependencies
- Depends on: RAP-641 (volunteer API, merged), RAP-176 (S4 application review, merged)
- Blocked by: none

## Risks
- Risk: API may need page_size increase for directory use → Mitigation: use large page_size (100) for directory view
