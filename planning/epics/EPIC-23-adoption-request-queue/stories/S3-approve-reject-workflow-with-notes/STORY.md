---
story: S3
epic: EPIC-23
ticket: RAP-112
title: "Approve/reject workflow with notes"
status: done
points: 5
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S3: Approve/reject workflow with notes

## Story
As a **staff member**, I want **approve/reject workflow with notes** so that **shelter operations are efficient and data-driven**.

## Description
Staff can approve or reject applications with mandatory notes.

## Acceptance Criteria

**Given** Given I am viewing an application
**When** When I click Approve or Reject
**Then** Then I must enter a note explaining the decision before confirming

**Given** Given I approve a request
**When** When confirmed
**Then** Then the animal status changes to reserved and the adopter is notified

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
