---
story: S4
epic: EPIC-21
ticket: RAP-103
title: "Session timeout and forced logout"
status: planned
points: 3
priority: P1
track: Backend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S4: Session timeout and forced logout

## Story
As a **system**, I want **session timeout and forced logout** so that **shelter operations are efficient and data-driven**.

## Description
Inactive sessions are automatically expired. Admins can force-logout any session.

## Acceptance Criteria

**Given** Given I am logged in
**When** When I am inactive for more than 30 minutes
**Then** Then my session is expired and I must re-authenticate

**Given** Given I am an admin
**When** When I view active sessions
**Then** Then I can force-logout any staff session

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-21
- Track: Backend
- Priority: P1
- Sprint: 1

## Story Points: 3
