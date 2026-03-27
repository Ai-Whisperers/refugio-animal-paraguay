---
story: S6
epic: EPIC-80
ticket: RAP-538
title: "Community feed"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S6: Community feed

## Story
As a **community member**, I want **to see activity feed** so that **I can follow rescue efforts and successes**.

## Description
Create chronological feed showing rescue community activity (new animals, campaigns, needs, success stories).

## Acceptance Criteria
- [ ] /community public page: chronological feed of activities
- [ ] Feed items: new animals listed by rescuers, new campaigns, new needs posted, success stories (animals adopted)
- [ ] Each item shows: timestamp, rescuer name, item type (icon), title, preview, "Learn more" link
- [ ] Pagination: load 20 items, support pagination/infinite scroll
- [ ] Filtering: filter by activity type (animals|campaigns|needs|successes), filter by location (within 100km radius)
- [ ] Sorting: newest first, option to sort by engagement (reactions/comments, optional)
- [ ] Real-time: new items appear in feed in real-time if user watching (WebSocket optional)
- [ ] Success stories: special highlight for animals adopted with before/after photos
- [ ] Responsive design: works on mobile

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Component test: feed renders correctly
- [ ] Component test: filtering works
- [ ] Component test: responsive
- [ ] Integration test: items appear in correct order
- [ ] Deployed to staging and verified

## Technical Notes
- Feed aggregation: query from animals, campaigns, needs, success stories (union of tables)
- Location filtering: use PostGIS or haversine distance
- Pagination: offset/limit
- Real-time: optional WebSocket for live updates
- Caching: cache feed (short TTL since frequently updated)

## Story Points: 5
