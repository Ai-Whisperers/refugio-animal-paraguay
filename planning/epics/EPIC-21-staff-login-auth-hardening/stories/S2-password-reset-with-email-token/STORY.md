---
story: S2
epic: EPIC-21
ticket: RAP-101
title: "Password reset with email token"
status: done
points: 5
priority: P0
track: Fullstack
sprint: 1
version: V4
created: 2026-03-26T19:06:04
---

# S2: Password reset with email token

## Story
As a **staff member**, I want **password reset with email token** so that **shelter operations are efficient and data-driven**.

## Description
Staff can request a password reset via email with a time-limited token.

## Acceptance Criteria

**Given** Given I click Forgot Password on the login page
**When** When I enter my registered email
**Then** Then I receive an email with a password reset link valid for 1 hour

**Given** Given I click the reset link in my email
**When** When I enter a new password meeting complexity requirements
**Then** Then my password is updated and I can log in with the new password

**Given** Given I have a reset token
**When** When the token has expired (>1 hour)
**Then** Then I see an error asking me to request a new reset link

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes
- Epic: EPIC-21
- Track: Fullstack
- Priority: P0
- Sprint: 1

## Story Points: 5
