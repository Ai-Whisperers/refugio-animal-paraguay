---
story: S3
epic: EPIC-22
ticket: RAP-107
title: "Animal status workflow (intake > available > reserved > adopted)"
status: planned
points: 5
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S3: Animal status workflow (intake > available > reserved > adopted)

## Story
As a **staff member**, I want **animal status workflow (intake > available > reserved > adopted)** so that **shelter operations are efficient and data-driven**.

## Description
Staff can change an animal's status through the defined lifecycle.

## Acceptance Criteria

**Given** Given I view an animal detail
**When** When I click Change Status
**Then** Then I see only the valid next statuses based on current state

**Given** Given I change status to adopted
**When** When I confirm
**Then** Then the status updates, a timestamp is recorded, and the change appears in the animal's history

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
