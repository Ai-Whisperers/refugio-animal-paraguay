# RAP-181 Plan

## Objective
Build a shift calendar view for staff in the Next.js admin panel, allowing staff to browse shifts by week, create new shifts, and see capacity at a glance.

## Description
Staff need a visual interface to manage volunteer shifts. This story adds an admin page at /admin/shifts with a weekly calendar view showing shifts grouped by day, capacity indicators, and quick-create functionality.

## Acceptance Criteria
- [ ] `/admin/shifts` page with weekly calendar view
- [ ] Shows shifts grouped by day with start/end time, role, capacity/slots_filled
- [ ] Week navigation (previous/next week)
- [ ] Quick-create shift form (modal or inline) for staff
- [ ] Status badges (open/full/cancelled/completed) with colors
- [ ] Empty state when no shifts in selected week
- [ ] Error boundary and loading state
- [ ] TypeScript types for Shift API responses
- [ ] Fetches from GET /api/shifts with date_from/date_to filters

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new page, calendar UI, API integration, TypeScript types

## Approach
1. Add Shift TypeScript types to frontend/src/types/api.ts
2. Create /admin/shifts/page.tsx with weekly calendar
3. Create ShiftCard component
4. Add navigation link in admin layout

## Dependencies
- Depends on: RAP-180 backend API (in review PR #306)
- Blocked by: None (frontend can be built against the API spec)
