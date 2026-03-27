---
story: S5
epic: EPIC-21
ticket: RAP-104
title: "Account lockout after failed attempts"
status: done
points: 2
priority: P2
track: Backend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S5: Account lockout after failed attempts

## Story
As a **system**, I want **account lockout after failed attempts** so that **shelter operations are efficient and data-driven**.

## Description
Accounts are temporarily locked after 5 consecutive failed login attempts.

## Acceptance Criteria

**Given** Given I enter wrong credentials 5 times
**When** When I try a 6th time
**Then** Then my account is locked for 15 minutes and I see a lockout message

**Given** Given my account is locked
**When** When 15 minutes have passed
**Then** Then I can attempt to log in again

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-21
- Track: Backend
- Priority: P2
- Sprint: 1

## Story Points: 2
