---
story: S1
epic: EPIC-51
ticket: RAP-250
title: "Dashboard API with aggregated metrics"
status: done
points: 5
priority: P0
track: Backend
sprint: 7
version: V10
created: 2026-03-26T19:06:04
completed: 2026-03-29
pr: 375
---

# S1: Dashboard API with aggregated metrics

## Story
As a **staff member**, I want **a real-time operational dashboard API** so that **I can monitor shelter metrics from live data**.

## Description
Implements GET /api/admin/operational-dashboard/metrics backed by live SQLAlchemy aggregate queries. Returns population breakdown by status, occupancy rate, intake/outcome counts for configurable period, species breakdown, and average length of stay.

## Acceptance Criteria
- [x] GET /api/admin/operational-dashboard/metrics returns live aggregated data
- [x] Returns population breakdown by status (intake, quarantine, available, foster, under_treatment, adopted, deceased)
- [x] Returns occupancy metrics (current count, capacity, occupancy_rate_pct)
- [x] Returns intake and outcome counts for configurable period (default 30 days)
- [x] Returns species breakdown (dog/cat/other)
- [x] Returns average length of stay for currently sheltered animals
- [x] Requires staff/admin JWT auth
- [x] 22 unit tests passing
- [x] Integration tests created (require live DB)

## Definition of Done
- [x] Code complete, peer reviewed (PR #375)
- [x] Unit tests written and passing (22 tests)
- [x] Integration tests created
- [x] Ruff and black clean

## Story Points: 5
