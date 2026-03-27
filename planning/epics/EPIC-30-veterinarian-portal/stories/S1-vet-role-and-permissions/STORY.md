---
story: S1
epic: EPIC-30
ticket: RAP-145
title: "Vet role and permissions"
status: done
points: 3
priority: P0
track: Backend
sprint: 2
version: V5
created: 2026-03-26T19:06:04
---

# S1: Vet role and permissions

## Story
As a **system**, I want **vet role and permissions** so that **shelter operations are efficient and data-driven**.

## Description
Add vet role to the auth system with appropriate permissions.

## Acceptance Criteria

**Given** Given a user has the vet role
**When** When they access the API
**Then** Then they can read/write medical records but cannot manage adoptions or finances

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-30
- Track: Backend
- Priority: P0
- Sprint: 2

## Story Points: 3
