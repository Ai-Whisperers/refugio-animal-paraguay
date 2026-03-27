---
story: S3
epic: EPIC-21
ticket: RAP-102
title: "Email verification on registration"
status: done
points: 3
priority: P1
track: Backend
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S3: Email verification on registration

## Story
As a **system**, I want **email verification on registration** so that **shelter operations are efficient and data-driven**.

## Description
New account registrations require email verification before the account is activated.

## Acceptance Criteria

**Given** Given a new staff account is created
**When** When the registration is saved
**Then** Then a verification email is sent with a unique token

**Given** Given I click the verification link
**When** When the token is valid
**Then** Then my account status changes to verified and I can log in

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
