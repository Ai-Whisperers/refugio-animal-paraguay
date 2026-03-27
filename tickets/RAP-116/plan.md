# RAP-116 Plan

## Objective
Create a donation history page with date, type, and currency filters for staff.

## Description
Staff need to view all donations with advanced filtering by date range, currency, payment method, and status. The backend GET /donations endpoint already exists with all required filters. This story implements the frontend page.

## Acceptance Criteria
- [ ] Donation history page at /admin/donations with paginated table
- [ ] Date range filter (from/to)
- [ ] Currency filter (EUR, PYG, USD)
- [ ] Payment method filter
- [ ] Status filter
- [ ] Running totals for filtered results
- [ ] Loading, error, and empty states

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [ ] Change impact ≤10 lines of actual code — NO, new page ~300 lines
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — new page but follows established patterns

## Approach
1. Create /admin/donations/page.tsx following existing admin page patterns
2. Use existing GET /donations API with filters
3. Follow Spanish label convention from other admin pages

## Dependencies
- Backend GET /donations endpoint (exists)
- Frontend api client (exists)

## Risks
- None significant — follows established patterns
