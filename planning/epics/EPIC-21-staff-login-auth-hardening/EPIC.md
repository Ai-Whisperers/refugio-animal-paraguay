---
epic: EPIC-21
title: "Staff Login & Auth Hardening"
sprint: 1
status: planned
points: 18
created: 2026-03-26T19:06:04
version: V4
---

# EPIC-21: Staff Login & Auth Hardening

## Overview
**Goal**: Password reset flow, email verification, session management, and staff login page. Foundation for all admin work.
**Why it matters**: Staff cannot access any admin functionality without a working login. This is the prerequisite for every other Sprint 1 epic.
**Target users**: Shelter staff, administrators

## Stories
- [ ] [S1] Staff login page with JWT auth flow (5 pts, P0, Frontend)
- [ ] [S2] Password reset with email token (5 pts, P0, Fullstack)
- [ ] [S3] Email verification on registration (3 pts, P1, Backend)
- [ ] [S4] Session timeout and forced logout (3 pts, P1, Backend)
- [ ] [S5] Account lockout after failed attempts (2 pts, P2, Backend)

## Total Points
18

## Dependencies
- Sprint 1 prerequisite epics (if any)

## Acceptance Criteria (Epic Level)
- [ ] All P0 stories completed
- [ ] All tests passing
- [ ] Deployed to staging and verified
