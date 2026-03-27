---
story: S7
epic: EPIC-80
ticket: RAP-539
title: "Donor choice interface"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S7: Donor choice interface

## Story
As a **donor**, I want **to browse rescuers and choose who to support** so that **I can support specific rescue efforts**.

## Description
Create rescuer directory where donors can search, filter, and choose rescuers to support.

## Acceptance Criteria
- [ ] /rescuers public page: directory of all verified rescuers
- [ ] Filtering: by location (within distance), specialty/focus, impact level (animals rescued count)
- [ ] Sorting: by activity (recent), supporters, animals rescued
- [ ] Rescuer cards: show: profile photo, name, location, "X animals rescued", mission statement, supporter count, verification badge, "Support" button
- [ ] Search: search by rescuer name
- [ ] Pagination: show 12 per page with pagination
- [ ] Responsive: grid layout on desktop, single column on mobile
- [ ] View profile: click card to view full rescuer profile (S2)
- [ ] Support action: "Support" button opens donation dialog

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Component test: directory renders
- [ ] Component test: filtering works
- [ ] Component test: sorting works
- [ ] Component test: responsive
- [ ] Integration test: correct rescuers displayed
- [ ] Deployed to staging and verified

## Technical Notes
- Rescuer listing: GET /api/rescuers endpoint, filter by verified status
- Location filtering: haversine distance calculation
- Caching: cache directory (1-hour TTL)
- Sorting: multiple options (created_at DESC, supporter_count DESC, animal_count DESC)

## Story Points: 5
