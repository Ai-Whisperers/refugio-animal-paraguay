# RAP-250 Plan

## Objective
Build a real-database-backed operational dashboard API endpoint for staff that surfaces current shelter metrics: animal population by status, occupancy, intake/outcome counts, species breakdown, and average length of stay.

## Description
The executive_kpi_dashboard uses hardcoded data. This story creates `/api/admin/operational-dashboard/metrics` backed by live SQL aggregation queries, giving staff real-time visibility into shelter operations.

## Acceptance Criteria
- [ ] GET /api/admin/operational-dashboard/metrics returns live aggregated data
- [ ] Returns population breakdown by status (intake, quarantine, available, foster, under_treatment, adopted, deceased)
- [ ] Returns occupancy metrics (current count, capacity, occupancy_rate_pct)
- [ ] Returns intake count for configurable period (default 30 days)
- [ ] Returns outcome count (adopted) for same period
- [ ] Returns species breakdown (dog/cat/other counts)
- [ ] Returns average length of stay for currently sheltered animals
- [ ] Requires staff/admin JWT auth
- [ ] Unit tests with mocked DB: ≥ 8 tests
- [ ] Integration tests for happy path and edge cases

## Complexity Assessment
**Track**: Complex — multiple SQL aggregation queries, new service layer, new router

**Assessment result**: Complex — 4+ new aggregation queries, new service, new router, tests

## Approach
1. Create `src/services/operational_metrics_service.py` with async aggregate queries
2. Create `src/api/operational_dashboard.py` with single metrics endpoint
3. Register router in `src/app.py`
4. Write tests

## Dependencies
- Depends on: Animal model (existing), auth (existing)
- Blocked by: nothing

## Risks
- Risk: No capacity field in DB → Mitigation: use configurable default (200) or query-param
