# RAP-250 Plan

## Objective
Implement the operational dashboard API endpoint that exposes aggregated shelter metrics (population breakdown, occupancy, species distribution, intake/adoption counts, average LOS).

## Description
EPIC-51 S1: Admin-facing REST endpoint under `/api/admin/operational-dashboard/metrics` that computes and returns shelter operational metrics in a single response. Staff-only auth. Supports configurable period window and capacity parameter.

## Acceptance Criteria
- [x] `GET /api/admin/operational-dashboard/metrics` returns 200 for staff users
- [x] Response includes population breakdown by all 7 AnimalStatus values
- [x] Response includes occupancy metrics (current count, capacity, occupancy_pct)
- [x] Response includes period intake/adoption/surrender/transfer counts (configurable window)
- [x] Response includes species breakdown
- [x] Response includes average LOS in days
- [x] Requires staff auth — returns 401/403 for unauthenticated/adopter users
- [x] `period_days` and `capacity` query params validated (ge=1, le=365 / ge=1, le=10000)
- [x] Unit tests ≥ 22 passing
- [x] Integration tests ≥ 15 passing
- [x] Ruff + mypy + black clean

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new service + router + schemas + 37 tests across two files, aggregated SQL queries.

## Approach
1. Create `src/schemas/operational_metrics.py` with Pydantic v2 response models
2. Create `src/services/operational_metrics_service.py` with async SQLAlchemy aggregate queries
3. Create `src/api/operational_dashboard.py` router
4. Register router in `src/app.py`
5. Write unit tests with AsyncMock DB
6. Write integration tests with AsyncClient

## Dependencies
- Depends on: EPIC-51 S0 setup (existing Animal model, auth middleware)
- Blocked by: nothing

## Risks
- Risk: SQLAlchemy case/cast syntax for aggregate counts → Mitigation: use `func.sum(cast(case(...), Integer))`
