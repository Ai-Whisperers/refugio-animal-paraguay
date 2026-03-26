# RAP-015 Plan

## Objective
Implement public animal browsing API with advanced filtering, name search, proper pagination, and enriched detail endpoint.

## Description
Create public (unauthenticated) endpoints for browsing available animals. The listing endpoint supports filtering by species, name search (case-insensitive partial match), and proper pagination with total counts. The detail endpoint returns complete animal info including photos. Only animals with status "available" are shown. This adds gender and size fields to the Animal model via migration.

## Acceptance Criteria
- [ ] Public listing endpoint returns only `available` animals
- [ ] Filtering by species works at DB level (case-insensitive)
- [ ] Name search with partial match (case-insensitive, ILIKE)
- [ ] Paginated response with items, total, page, size, pages
- [ ] Configurable page size (default 20, max 100)
- [ ] Detail endpoint returns complete animal with photos
- [ ] 404 for non-existent or non-available animals on detail
- [ ] Gender and size fields added to Animal model
- [ ] No authentication required on public endpoints
- [ ] Unit and integration tests with 80%+ coverage

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — New public router, schema migration, pagination wrapper, 8+ test cases.

## Approach
1. Add gender/size enum + columns to Animal model via Alembic migration
2. Create public browsing schemas (response, paginated wrapper)
3. Create public browsing router at /api/v1/public/animals
4. Implement list endpoint with filters + pagination + search
5. Implement detail endpoint with photo data
6. Write tests (unit for schemas, integration for endpoints)
7. Run quality gates

## Dependencies
- Depends on: RAP-003/RAP-004 (Animal CRUD) — delivered
- Blocks: Frontend animal browsing components

## Risks
- Risk: Migration conflicts with other branches → Mitigation: Check migration history first
