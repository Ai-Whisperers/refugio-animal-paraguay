---
story: S4
epic: EPIC-85
ticket: RAP-576
title: "Castration counter widget"
status: ready
points: 3
priority: P0
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S4: Castration counter widget

## Story
As a **visitor**, I want **to see how many animals have been castrated** so that **I understand the castration program's impact**.

## Description
Create reusable CastrationCounter component displaying large number of castrated animals. Placed on homepage, castration campaign pages, and impact page. Shows number and optional target.

## Acceptance Criteria
- [ ] CastrationCounter component created with props: {count, target (optional), label (default: "animales castrados")}
- [ ] Component displays large bold number (font-size: 4rem on desktop)
- [ ] Component displays label text: "X animales castrados"
- [ ] Optional target display: if target prop provided, show "X de Y meta" below counter
- [ ] Progress bar: if target provided, show progress bar filling to target percentage
- [ ] Component animates on mount (count-up animation from 0 to current number)
- [ ] Data source: counter fetches from GET /api/stats/public.total_castrated
- [ ] Component reusable: can be placed on homepage, campaign pages, impact page
- [ ] Mobile responsive: font size scales on mobile
- [ ] Accessibility: ARIA live region announces the count, proper semantic HTML
- [ ] Unit tests: verify data fetching and rendering

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: verify counter displays correct number
- [ ] E2E test: navigate to pages with counter, verify animation
- [ ] Responsive design verified
- [ ] Accessibility audit passed
- [ ] Deployed to staging and verified

## Technical Notes
- Create reusable component with flexible props
- Use react-countup for count animation
- Fetch data from /api/stats/public (cached)
- Optional props for target and label customization
- Consider React.memo to prevent unnecessary re-renders

## Story Points: 3
