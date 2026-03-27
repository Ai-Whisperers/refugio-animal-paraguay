---
story: S1
epic: EPIC-22
ticket: RAP-105
title: "Animal list with search, sort, pagination"
status: done
points: 5
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S1: Animal list with search, sort, pagination

## Story
As a **staff member**, I want **animal list with search, sort, pagination** so that **shelter operations are efficient and data-driven**.

## Description
Staff can view all animals in a paginated table with search and sort capabilities.

## Acceptance Criteria

**Given** Given I am on the animal management page
**When** When I view the list
**Then** Then I see a paginated table of all animals with name, species, status, intake date

**Given** Given I type in the search bar
**When** When I enter a partial name or ID
**Then** Then the list filters in real-time to matching animals

**Given** Given I click a column header
**When** When I click name or date
**Then** Then the list sorts ascending/descending by that column

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-22
- Track: Frontend
- Priority: P0
- Sprint: 1

## Story Points: 5
