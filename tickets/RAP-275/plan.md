# RAP-275 Plan

## Objective
Implement a dedicated adopter adoption status page in the portal, providing adopters with a detailed, focused view of all their adoption applications and current status.

## Description
The unified portal dashboard has a basic applications section. This story adds a dedicated `/portal/adoptions` route with a richer adopter-focused view: application timeline, detailed status per animal, decision notes, and clear next-step guidance. A new backend endpoint `/portal/adoptions` returns enriched adoption data.

## Acceptance Criteria
- [ ] GET /portal/adoptions endpoint returns all adoption applications for the authenticated user (matched by email)
- [ ] Each application includes: id, animal name/species, submitted date, status, decision notes, decided_at
- [ ] Frontend page at /portal/adoptions renders all applications with status badges
- [ ] Empty state shows encouragement to browse animals
- [ ] Status progression is visually clear (pending → approved/rejected)
- [ ] Unit and integration tests passing (80%+ coverage on new code)
- [ ] ruff, black, pytest all pass

## Complexity Assessment
**Track**: Simple Fix — 2-3 files (backend endpoint + service + frontend page), focused feature, no migrations needed.

**Assessment result**: Simple Fix — read-only endpoint that aggregates existing adoption data + frontend display page.

## Approach
1. Add `AdopterApplicationDetail` schema and `/portal/adoptions` endpoint
2. Extend dashboard service with `get_adopter_applications` helper
3. Create `frontend/src/app/portal/adoptions/page.tsx`
4. Write unit tests for the service helper and integration test for the endpoint

## Dependencies
- Depends on: RAP-502 (portal dashboard — PR #154 merged)
- Blocked by: none

## Risks
- None significant — purely additive, read-only changes
