# RAP-270 Plan

## Objective
Build a frontend admin page for viewing audit logs with filtering by action, resource type, date range, and user ID.

## Description
EPIC-55 S1 (P0). Backend API at `/admin/audit-logs` already exists with full filtering support. This story delivers the admin UI — a paginated table with filter controls, empty/error states, and navigation. UI follows existing admin page conventions (donors, donations pages).

## Acceptance Criteria
- [ ] Admin page at `/admin/audit-logs` renders a paginated table of audit log entries
- [ ] Filters: action, resource_type, start_date, end_date (user_id optional, advanced)
- [ ] Empty state when no logs match filters
- [ ] Error state with retry button on API failure
- [ ] Pagination controls (previous/next, page info)
- [ ] Admin-only access (redirect to login if unauthenticated)
- [ ] AdminSidebar navigation item added for "Audit Logs"
- [ ] Unit tests for the page component

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified — UI page missing, backend ready
- [x] Solution affects ≤3 files — page.tsx + sidebar update
- [x] Change impact ≤10 lines of actual code — more but well-scoped
- [x] Low risk of side effects
- [x] Solution pattern is well-understood — mirrors donors/donations pages

**Assessment result**: Simple Fix — straightforward frontend page following established patterns

## Approach
1. Create `/admin/audit-logs/page.tsx` with filter controls and paginated table
2. Add "Registros de Auditoria" link to AdminSidebar
3. Write tests

## Dependencies
- Depends on: Backend `/admin/audit-logs` API (already in src/api/admin.py)

## Risks
- Risk: Audit logs table may be empty in test environments → Mitigation: Handle empty state gracefully
