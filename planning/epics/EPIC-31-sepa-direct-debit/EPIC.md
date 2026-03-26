---
epic: EPIC-31
title: "SEPA Direct Debit"
sprint: 3
status: planned
points: 21
created: 2026-03-26T19:06:04
version: V6
---

# EPIC-31: SEPA Direct Debit

## Overview
**Goal**: EU bank transfer support via Stripe SEPA. Enables European donors to contribute via bank debit.
**Target users**: Shelter staff, administrators, donors, adopters, veterinarians, volunteers

## Stories
- [ ] [S1] SEPA payment method setup in Stripe (5 pts, P0, Backend)
- [ ] [S2] SEPA mandate creation flow (5 pts, P0, Fullstack)
- [ ] [S3] SEPA webhook handling (succeeded, failed) (5 pts, P0, Backend)
- [ ] [S4] SEPA payment status tracking (3 pts, P1, Backend)
- [ ] [S5] SEPA-specific donor notifications (3 pts, P1, Backend)

## Total Points
21

## Acceptance Criteria (Epic Level)
- [ ] All P0 stories completed
- [ ] All tests passing
- [ ] Deployed to staging and verified
