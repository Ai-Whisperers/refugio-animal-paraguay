---
story: S5
epic: EPIC-24
ticket: RAP-119
title: "Missing GET /donors list endpoint"
status: planned
points: 2
priority: P0
track: Backend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S5: Missing GET /donors list endpoint

## Story
As a **system**, I want **missing get /donors list endpoint** so that **shelter operations are efficient and data-driven**.

## Description
Add the missing donors list API endpoint that the frontend needs.

## Acceptance Criteria

**Given** Given I call GET /api/v1/donors
**When** When I provide valid auth
**Then** Then I receive a paginated list of donors with search and filter support

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-24
- Track: Backend
- Priority: P0
- Sprint: 1

## Story Points: 2
