# RAP-251 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 00:00

## Current Focus
Implementing frontend KPI cards page for operational dashboard.

## Technical State
- Backend API: `GET /api/admin/operational-dashboard/metrics` — live and returning: population, occupancy, period, species, avg_los_days
- Frontend target: `/admin/operational-dashboard/page.tsx`
- Pattern reference: `/admin/analytics/donaciones/page.tsx`
- Auth: uses JWT Bearer token from localStorage (same as other admin pages)

## Next Steps
1. Create page.tsx with KPI card components
2. Write Vitest tests
3. Run quality gates
4. Push and create PR

## Blockers
None

## Key Decisions Made
- Page lives at /admin/operational-dashboard (not /admin/dashboard which already exists)
- Uses same fetch pattern as other analytics pages
- Period selector as a dropdown (7/14/30/90 days)
