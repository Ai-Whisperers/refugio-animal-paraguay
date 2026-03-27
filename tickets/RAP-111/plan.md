# RAP-111 Plan

## Objective
Create a detail view page for individual adoption requests showing full adopter info and animal details.

## Acceptance Criteria
- [ ] Detail page at /admin/adoptions/[id]
- [ ] Shows complete adoption request info (status, dates, notes)
- [ ] Shows full adopter profile (name, email, phone, address)
- [ ] Shows requested animal info with photo
- [ ] Loading and error states
- [ ] Back navigation to adoption list
- [ ] Auth-protected

## Complexity Assessment
**Track**: Complex — Dynamic route, multiple API calls, rich layout

## Approach
1. Create /admin/adoptions/[id]/page.tsx
2. Fetch adoption request, adopter, and animal data
3. Display in organized sections
