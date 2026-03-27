---
story: S8
epic: EPIC-81
ticket: RAP-550
title: "Fund management dashboard"
status: ready
points: 5
priority: P2
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S8: Fund management dashboard

## Story
As an **admin**, I want **to track and manage all donations** so that **I can ensure proper allocation and transparency**.

## Description
Create comprehensive admin dashboard for monitoring donations, allocations, and fund health.

## Acceptance Criteria
- [ ] /admin/funds page: main dashboard showing fund overview
- [ ] Summary cards: total donations (all-time), total allocated, unallocated amount (balance), allocation rate (%), pending allocations
- [ ] Breakdown by type: pie chart or table showing donations by target type (general, animal, rescuer, clinic, campaign, need)
- [ ] Unallocated funds: list of donations waiting allocation, sortable, filterable
- [ ] Allocation rate: visual indicator, goal is >80%
- [ ] Pending allocations: list of allocations awaiting approval
- [ ] Search/filter: search by donor name, target, date range
- [ ] Export: "Export Fund Report" button generates CSV with: date, donor, amount, target, allocation status, allocated_amount
- [ ] Trending: chart showing donations over time (daily/weekly/monthly)
- [ ] Fund health: "Allocate funds regularly to maintain transparency" message if unallocated > 20%

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test calculations, aggregations
- [ ] Component test: dashboard renders
- [ ] Component test: charts display correctly
- [ ] Integration test: numbers accurate
- [ ] Integration test: CSV export format correct
- [ ] Manual testing: dashboard usage
- [ ] Deployed to staging and verified

## Technical Notes
- Dashboard data: GET /api/admin/funds/dashboard endpoint
- Aggregations: sum donations, sum allocations, group by target_type
- Charts: Recharts for visualization
- CSV export: use csv module, return as download
- Caching: cache dashboard data (1-hour TTL) since calculations expensive
- Trending: query daily totals, group by date

## Story Points: 5
