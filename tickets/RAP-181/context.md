# RAP-181 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-28 15:16

## Current Focus
Building shift calendar admin page in Next.js 14 (App Router).

## Technical State
- Branch: feature/RAP-181-shift-calendar-view-staff
- Frontend: frontend/src/app/admin/shifts/page.tsx

## Next Steps
1. Add TypeScript types for Shift
2. Create admin shifts page with calendar
3. Create ShiftCreateModal component
4. Update admin nav

## Blockers
None

## Key Decisions Made
- Weekly view (Mon-Sun) as default — simplest useful calendar
- Shifts grouped by day, sorted by start_time
- Uses API date filters (date_from/date_to) for efficient data loading
