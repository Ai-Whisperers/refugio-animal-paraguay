---
story: S2
epic: EPIC-25
ticket: RAP-121
title: "Role-based menu visibility (admin vs staff)"
status: done
points: 3
priority: P0
track: Frontend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S2: Role-based menu visibility (admin vs staff)

## Story
As a **staff member**, I want **role-based menu visibility (admin vs staff)** so that **shelter operations are efficient and data-driven**.

## Description
Menu items are shown/hidden based on the user's role.

## Acceptance Criteria

**Given** Given I am logged in as staff
**When** When I view the sidebar
**Then** Then I see only the menu items my role permits

**Given** Given I am logged in as admin
**When** When I view the sidebar
**Then** Then I see all menu items including settings and user management

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-25
- Track: Frontend
- Priority: P0
- Sprint: 1

## Story Points: 3
