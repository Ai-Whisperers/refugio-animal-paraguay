---
story: S2
epic: EPIC-85
ticket: RAP-574
title: "Homepage live statistics"
status: ready
points: 3
priority: P0
track: Frontend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S2: Homepage live statistics

## Story
As a **visitor**, I want **to see real statistics on homepage** so that **I'm impressed by the impact**.

## Description
Replace hardcoded statistics on homepage with live data from /stats/public API. Animate numbers counting up on page load for visual impact.

## Acceptance Criteria
- [ ] Homepage statistics section fetches from GET /api/stats/public on mount
- [ ] Statistics displayed: rescued animals count, adopted count, volunteers count, donations total (with currency)
- [ ] Numbers animate with count-up effect: start from 0, count to final number over 2 seconds
- [ ] Animation only plays on page load, not on every re-render
- [ ] Fallback values used if API fails (show cached/hardcoded defaults)
- [ ] API call respects 5-minute cache (browser cache control)
- [ ] Statistics update if user refreshes page (new API call)
- [ ] Loading state: show skeleton placeholders while fetching
- [ ] Error state: show fallback values and log error (don't show error to user)
- [ ] Mobile responsive: statistics displayed in 2x2 grid on mobile, 4 across on desktop
- [ ] Unit tests: verify data fetching and rendering

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: fetch data, verify numbers displayed
- [ ] E2E test: navigate to homepage, verify stats animate
- [ ] Animation tested across browsers
- [ ] Fallback behavior tested (API error)
- [ ] Responsive design verified
- [ ] Deployed to staging and verified

## Technical Notes
- Use react-countup library for smooth animations
- Implement with React Query or SWR for data fetching
- Use useEffect with dependency array to avoid re-fetching
- Cache policy: Cache-Control: public, max-age=300
- Consider Intersection Observer to only animate when visible

## Story Points: 3
