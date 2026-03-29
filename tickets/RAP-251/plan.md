# RAP-251 Plan

## Objective
Implement a KPI cards frontend page showing real-time occupancy, intake, and outcome metrics from the operational dashboard API.

## Description
Create a new Next.js page `/admin/operational-dashboard` that fetches data from `GET /api/admin/operational-dashboard/metrics` and renders live KPI cards: occupancy rate, current population, intake count, outcome count, species breakdown, and average length of stay.

## Acceptance Criteria
- [ ] Page `/admin/operational-dashboard` renders KPI cards with live data
- [ ] Cards show: occupancy rate (%), current animal count, intake count (30d), outcome count (30d), species breakdown (dog/cat/other), avg length of stay
- [ ] Loading state shown while fetching
- [ ] Error state shown on API failure
- [ ] Period selector (7/14/30/90 days) updates the data
- [ ] Requires authentication (redirects to login if unauthenticated)
- [ ] Unit tests for KPI card components (Vitest)

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — new frontend page with multiple components and tests. Follows well-understood Next.js App Router patterns.

## Approach
1. Create `/frontend/src/app/admin/operational-dashboard/page.tsx` with KPI card layout
2. Fetch from `/api/admin/operational-dashboard/metrics` with JWT auth
3. Show loading/error states
4. Add period selector for 7/14/30/90 days
5. Write Vitest unit tests for the component

## Dependencies
- Depends on: RAP-250 (PR #375 merged) — dashboard API
- Blocked by: nothing

## Risks
- Risk: Auth token handling in Next.js App Router → Mitigation: follow existing page patterns (e.g. admin/analytics/donaciones)
