# RAP-538 Plan

## Objective
Build a public community feed aggregating recent animals, campaigns, needs, and success stories.

## Description
S6 of EPIC-80 (Rescuer Network). Community members visit /community to discover activity across the shelter network — new animals listed, active campaigns, open needs, and adoption success stories. Chronological feed with type-based filtering and location radius filter.

## Acceptance Criteria
- [x] /community public page: chronological feed of activities
- [x] Feed items: new animals, new campaigns, new needs, success stories
- [x] Each item shows: timestamp, badge (item type), title, preview, "Learn more" link
- [x] Pagination: load 20 items, load-more button
- [x] Filtering: filter by activity type (animals|campaigns|needs|successes)
- [x] Location filter: lat/lng/radius_km query params (items without coords pass through)
- [x] Sorting: newest first
- [x] Responsive design: works on mobile (CSS grid with sm:/lg: breakpoints)
- [x] Pre-existing import error in app.py (admin_router) fixed

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — Fullstack (service + API + frontend), 4 data sources, location filtering

## Approach
1. Service: `src/services/community_feed_service.py` — aggregates from 4 tables, haversine location filtering, paginated merge
2. API: `src/api/community_feed.py` — GET /api/community/feed with query params
3. Register in app.py (fix pre-existing admin_router import bug)
4. Frontend: `frontend/src/app/community/page.tsx` — responsive grid with filter bar, load-more

## Dependencies
- Depends on: RAP-534 (Rescuer profile — slug), RAP-535 (Animal listing), RAP-537 (Needs board)

## Risks
- Pre-existing community_needs admin_router import error blocks all unit tests → fixed as part of this PR
