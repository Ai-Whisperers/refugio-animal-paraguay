---
story: S1
epic: EPIC-24
ticket: RAP-115
title: "Donor list with search and export"
status: planned
points: 5
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S1: Donor list with search and export

## Story
As a **staff member**, I want **donor list with search and export** so that **shelter operations are efficient and data-driven**.

## Description
Staff can view all donors in a searchable, exportable list.

## Acceptance Criteria

**Given** Given I navigate to donor management
**When** When the page loads
**Then** Then I see all donors with name, email, total donated, last donation date

**Given** Given I click Export
**When** When I choose CSV
**Then** Then a CSV file downloads with all donor records

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-24
- Track: Frontend
- Priority: P0
- Sprint: 1

## Story Points: 5
