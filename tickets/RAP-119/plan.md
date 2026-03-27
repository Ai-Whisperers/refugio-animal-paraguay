# RAP-119 Plan

## Objective
Add a GET /donors list endpoint with search, filtering, pagination, and CSV export for the staff admin panel.

## Description
The donors router currently only supports POST (create) and GET by ID. The frontend donor management page (EPIC-24 S1) needs a paginated, searchable list of donors. This backend story unblocks all EPIC-24 frontend stories.

## Acceptance Criteria
- [ ] GET /donors returns paginated list of donors (staff only)
- [ ] Search by name or email via query parameter
- [ ] Filter by country code
- [ ] Sort by full_name, email, or created_at (asc/desc)
- [ ] Offset/limit pagination matching existing patterns
- [ ] GET /donors/export returns CSV export (staff only)
- [ ] Unit tests for all new endpoints (80%+ coverage)
- [ ] Integration tests for happy path and edge cases

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria
- [x] Single, clear root cause identified (missing endpoint)
- [x] Solution affects <=3 files (router, schemas, tests)
- [ ] Change impact <=10 lines of actual code (more, but straightforward)
- [x] Low risk of side effects
- [x] Solution pattern is well-understood (follows donations list pattern)

**Assessment result**: Complex — more than 10 lines, but well-patterned

## Approach
1. Add DonorListResponse schema with donation count summary
2. Add GET /donors list endpoint with search/filter/pagination
3. Add GET /donors/export CSV endpoint
4. Write unit and integration tests

## Dependencies
- None (unblocks RAP-115, RAP-116, RAP-117)

## Risks
- Risk: Search performance on large donor tables -> Mitigation: Use ILIKE with indexed columns
