# RAP-256 Plan

## Objective
Create a Next.js admin page for the Fund Allocation vs Budget Report, showing donation totals, allocation breakdown by fund type, and expense comparison across categories.

## Acceptance Criteria
- [ ] Admin page at /admin/financial-reporting shows fund allocation report
- [ ] Displays donation summary by currency (EUR/PYG/USD)
- [ ] Shows allocation breakdown: allocated vs unallocated vs expenses
- [ ] Category bar chart showing donations vs expenses by category
- [ ] Export link to CSV (uses existing /admin/funds/export endpoint)
- [ ] Loading state and error boundary
- [ ] Auth: staff role required (redirects if not authenticated)

## Complexity Assessment
**Track**: Simple Fix — single frontend page, ≤3 files.

## Approach
1. Create `frontend/src/app/admin/financial-reporting/page.tsx`
2. Fetch from donation summary API (RAP-255) + admin fund dashboard API
3. Render KPI cards + allocation bar + category breakdown table

## Dependencies
- RAP-255 donation summary API (new /api/admin/financial-reporting/donation-summary)
- Existing /admin/funds/dashboard API
