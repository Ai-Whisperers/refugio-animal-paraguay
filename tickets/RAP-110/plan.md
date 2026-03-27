# RAP-110 Plan

## Objective
Create an admin page showing all adoption requests with status filters, search, and pagination.

## Description
Staff need to view and manage adoption requests through the admin interface. This page lists all adoption requests with filtering by status (pending, approved, rejected, cancelled), sorted by submission date.

## Acceptance Criteria
- [ ] Admin adoption queue page at /admin/adoptions
- [ ] Displays all adoption requests with key info (adopter, animal, status, date)
- [ ] Status filter tabs (All, Pending, Approved, Rejected, Cancelled)
- [ ] Sorted by submission date (newest first)
- [ ] Loading and error states handled
- [ ] Empty state when no requests match filters
- [ ] Auth-protected (redirects to login if not authenticated)

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — Multiple files (types, page component, navigation), frontend patterns to follow, API integration.

## Approach
1. Add AdoptionRequest types to frontend types/api.ts
2. Create /admin/adoptions/page.tsx with list, filters, pagination
3. Follow existing admin/animals page patterns
4. Add navigation link from admin dashboard

## Dependencies
- Backend adoption requests API (exists)
- Admin layout (exists)

## Risks
- Risk: API response shape mismatch → Mitigation: Verified schema matches backend
