# RAP-029 Plan

## Objective
Implement public (unauthenticated) animal browsing endpoints for the public portal.

## Description
The public portal needs endpoints where visitors can browse available animals and view individual animal profiles. These endpoints require no authentication, only return animals with status='available', and support comprehensive filtering (species, breed, size, gender, age range) plus name search with pagination.

## Acceptance Criteria
- [x] GET /public/animals returns paginated list of available animals only
- [x] Filtering by species, breed (case-insensitive), size, gender, age range works at DB level
- [x] Name search with partial, case-insensitive matching
- [x] Pagination with page/page_size params and total count metadata
- [x] GET /public/animals/{id} returns full animal detail with photos
- [x] Non-available animals return 404 on detail endpoint
- [x] No authentication required
- [x] Consistent JSON with explicit nulls
- [x] breed, size, gender columns added to animals table via migration

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria
- [ ] Single, clear root cause identified
- [ ] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code — NO, new router + schemas + migration
- [ ] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — new public API surface, schema migration, 8+ files touched

## Approach
1. Add breed, size, gender columns to animals table (migration 008)
2. Update Animal model and existing schemas
3. Create public browsing schemas (list item, detail, paginated response)
4. Create public router with listing + detail endpoints
5. Register router in app.py
6. Write unit and integration tests

## Dependencies
- Depends on: EPIC-1 (animal models), RAP-003/004 (CRUD API), RAP-008 (photos)
- Blocked by: none

## Risks
- Risk: DB migration on existing columns → Mitigation: idempotent migration with IF NOT EXISTS
