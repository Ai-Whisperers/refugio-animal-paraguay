---
story: S3
epic: EPIC-85
ticket: RAP-575
title: "Public impact page"
status: done
points: 5
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S3: Public impact page

## Story
As a **visitor**, I want **to see detailed impact statistics and trends** so that **I understand the organization's progress over time**.

## Description
Create /impact page with charts showing historical trends. Data visualized as bar charts, line charts showing monthly aggregates for the last 12 months.

## Acceptance Criteria
- [ ] /impact page created with header "Our Impact"
- [ ] GET /api/stats/impact endpoint returns monthly aggregates: animals_rescued (count), adoptions_completed (count), castrations_performed (count), donations_total (amount) for last 12 months
- [ ] Data organized by month: [{month, year, animals_rescued, adoptions_completed, castrations, donations}]
- [ ] Chart 1: Animals rescued by month (bar chart, blue color)
- [ ] Chart 2: Donations by month (line chart, green color, shows trend)
- [ ] Chart 3: Adoptions by month (bar chart, orange color)
- [ ] Chart 4: Castrations cumulative (line chart, shows increasing total)
- [ ] Charts responsive: full-width on mobile, 2x2 grid on desktop
- [ ] Charts interactive: hover shows exact values, click for details
- [ ] Use Recharts library for chart rendering
- [ ] Summary statistics at top: total rescued (all time), total adopted, total castrated, total donated
- [ ] Share button on page for social sharing
- [ ] Page cached: GET /api/stats/impact cached for 1 hour
- [ ] Accessibility: alt text for charts, semantic HTML structure

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: verify monthly data calculation
- [ ] E2E test: navigate to /impact, verify charts display
- [ ] Chart interactivity tested
- [ ] Responsive design verified on mobile/tablet/desktop
- [ ] Accessibility audit passed
- [ ] Deployed to staging and verified

## Technical Notes
- Use Recharts for React chart rendering
- Fetch monthly data via GET /api/stats/impact
- Consider caching monthly data (1 hour TTL)
- Add data validation: ensure 12 months of data
- Handle missing months gracefully (show as 0 or skip)

## Story Points: 5
