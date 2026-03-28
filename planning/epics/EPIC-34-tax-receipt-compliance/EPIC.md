---
epic: EPIC-34
title: "Tax Receipt & Compliance"
sprint: 3
status: done
points: 21
created: 2026-03-26T19:06:04
version: V6
---

# EPIC-34: Tax Receipt & Compliance

## Overview
**Goal**: Automated tax receipt generation for EU donors. Dutch ANBI compliance. Annual donation summaries.
**Target users**: Shelter staff, administrators, donors, adopters, veterinarians, volunteers

## Stories
- [x] [S1] Tax receipt PDF template (EU format) (5 pts, P0, Fullstack) — DONE (PR #294)
- [x] [S2] Annual donation summary generation (5 pts, P1, Backend) — DONE (PR #295)
- [x] [S3] ANBI compliance documentation (3 pts, P1, Backend) — DONE (PR #296)
- [x] [S4] Donor tax ID (BSN/TIN) secure storage (3 pts, P1, Backend) — DONE (PR #297)
- [x] [S5] Batch receipt generation and email (5 pts, P2, Backend) — code done, PR #298 needs conflict resolution (src/app.py)

## Total Points
21

## Acceptance Criteria (Epic Level)
- [x] All P0 stories completed
- [x] All tests passing
- [ ] Deployed to staging and verified (blocked: GitHub Actions billing issue)
