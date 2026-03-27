# RAP-115 Plan

## Objective
Create a staff-facing donor list page with search, filters, sorting, pagination, and CSV export.

## Acceptance Criteria
- [ ] Staff can view all donors with name, email, total donated, country
- [ ] Search by name or email
- [ ] Filter by country
- [ ] Sortable columns (name, email, created_at)
- [ ] Pagination
- [ ] CSV export download
- [ ] Loading, error, and empty states
- [ ] Spanish labels

## Complexity Assessment
**Track**: Complex — full page with data table, search, filters, export

## Approach
Follow existing admin animals page pattern. Server-side search/filter via GET /donors endpoint.

## Dependencies
- RAP-119 (GET /donors endpoint) — PR #102
