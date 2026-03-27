---
story: S1
epic: EPIC-23
ticket: RAP-110
title: "Adoption request list with status filters"
status: done
points: 5
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S1: Adoption request list with status filters

## Story
As a **staff member**, I want **adoption request list with status filters** so that **shelter operations are efficient and data-driven**.

## Description
Staff can view all adoption requests with filtering by status.

## Acceptance Criteria

**Given** Given I navigate to the adoption queue
**When** When the page loads
**Then** Then I see all pending requests sorted by submission date

**Given** Given I click a status filter tab
**When** When I select 'Under Review'
**Then** Then only requests with that status are shown

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-23
- Track: Frontend
- Priority: P0
- Sprint: 1

## Story Points: 5
