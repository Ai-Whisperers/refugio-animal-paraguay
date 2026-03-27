---
epic: EPIC-48
title: "Two-Factor Authentication"
sprint: 6
status: planned
points: 19
created: 2026-03-26T19:06:04
version: V9
---

# EPIC-48: Two-Factor Authentication

## Overview
**Goal**: TOTP-based 2FA for staff accounts. QR code setup, backup codes, enforcement policies.
**Target users**: Shelter staff, administrators, donors, adopters, veterinarians, volunteers

## Stories
- [ ] [S1] TOTP secret generation and verification (5 pts, P0, Backend)
- [ ] [S2] 2FA setup flow with QR code (5 pts, P0, Frontend)
- [ ] [S3] Backup codes generation and usage (3 pts, P1, Backend)
- [ ] [S4] 2FA enforcement for admin role (3 pts, P1, Backend)
- [ ] [S5] 2FA recovery flow (3 pts, P2, Fullstack)

## Total Points
19

## Acceptance Criteria (Epic Level)
- [ ] All P0 stories completed
- [ ] All tests passing
- [ ] Deployed to staging and verified
