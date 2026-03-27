---
epic: EPIC-75
title: "Frontend Stability & Error Recovery"
status: ready
priority: 97
sprint: priority
version: V3.1
points: 18
created: 2026-03-27
---

# EPIC-75: Frontend Stability & Error Recovery

## Overview

**Goal**: Fix critical frontend bugs and add proper error boundaries and loading states to all pages.

**Why it matters**: Frontend bugs block users from core features (donations, adoption). Error recovery improves user experience and reduces support load.

**Target users**: Website visitors, adopters, donors.

## Scope

### In Scope
- Add error boundaries (error.tsx, not-found.tsx) to all route segments
- Fix /animals page 404 rendering bug
- Integrate Stripe.js Elements into DonationForm
- Add loading and error states to all client pages
- Add centralized API error handling

### Out of Scope
- E2E testing (Playwright/Cypress) — separate epic
- Mobile app — future release
- Dark mode/theme switching — not critical

## Features

- [ ] RAP-420: Add error.tsx and not-found.tsx boundaries — 3 pts
- [ ] RAP-421: Fix /animals page 404 rendering bug — 5 pts
- [ ] RAP-422: Integrate Stripe.js Elements into DonationForm — 5 pts
- [ ] RAP-423: Add loading and error states to all client pages — 3 pts
- [ ] RAP-424: Add centralized API error handling in frontend — 2 pts

## Dependencies

- Depends on: EPIC-73 (standardized error responses from backend)
- Blocks: V3.1 release; user-facing feature stability
- Related: EPIC-72 (frontend component tests)

## Key Decisions Made

1. **Error boundaries**: App-level + route-level (granular error handling)
2. **Stripe integration**: Use Stripe Elements (not deprecated Stripe.js v2)
3. **State management**: SWR for data fetching (already in use)
4. **Loading UI**: Skeleton components from Tailwind UI
5. **Error messages**: Spanish + English (locale-aware)

## Risks

- **Risk**: Stripe sandbox keys need to be rotated in production
  → **Mitigation**: Use environment variables, rotate quarterly

- **Risk**: Breaking changes in Stripe API
  → **Mitigation**: Pin Stripe.js version, test on upgrades

---

## Acceptance Criteria (Epic Level)

The epic is complete when:

- [ ] All 5 stories merged to develop
- [ ] Error boundaries on all routes (no white page errors)
- [ ] /animals page renders animals list (not 404)
- [ ] DonationForm accepts Stripe card input
- [ ] All pages have loading spinners during data fetch
- [ ] All pages have error messages with retry buttons
- [ ] API errors handled consistently (toast messages, redirects)
- [ ] Frontend component tests pass (RAP-409)
- [ ] Manual testing on staging verified

---

## Definition of Done (Epic)

- [ ] All user stories complete and merged
- [ ] Manual smoke test: can view animals, donate, submit adoption request
- [ ] Stripe payment flow works end-to-end
- [ ] No console errors or warnings
- [ ] Component tests pass (coverage ≥ 70%)
- [ ] Code review approved
- [ ] Deployed to staging and verified

---

*Last updated: 2026-03-27*
*Owner: Frontend Stability Squad*
