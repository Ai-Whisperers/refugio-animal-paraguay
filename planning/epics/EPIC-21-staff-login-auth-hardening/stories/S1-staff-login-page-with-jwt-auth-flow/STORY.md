---
story: S1
epic: EPIC-21
ticket: RAP-100
title: "Staff login page with JWT auth flow"
status: planned
points: 5
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S1: Staff login page with JWT auth flow

## Story
As a **staff member**, I want **staff login page with jwt auth flow** so that **shelter operations are efficient and data-driven**.

## Description
Staff member can log in via a dedicated admin login page that authenticates against the existing JWT backend.

## Acceptance Criteria

**Given** Given I navigate to /admin/login
**When** When I enter valid staff credentials and click Login
**Then** Then I receive a JWT token and am redirected to the admin dashboard

**Given** Given I am on the login page
**When** When I enter invalid credentials
**Then** Then I see an error message and remain on the login page

**Given** Given I am authenticated
**When** When my JWT token expires
**Then** Then I am redirected to the login page with a session expired message

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-21
- Track: Frontend
- Priority: P0
- Sprint: 1

## Story Points: 5
