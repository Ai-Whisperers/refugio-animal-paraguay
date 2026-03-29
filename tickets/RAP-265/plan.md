# RAP-265 Plan

## Objective
Extend the impact report data aggregation service to include volunteer hours and active foster placement metrics for a comprehensive shelter impact picture.

## Description
The shelter's impact report needs to cover all dimensions of shelter operations. The base service (RAP-061) covers animals, adoptions, donations, fund allocation, and performance metrics. This ticket extends it to include volunteer contributions (active volunteers, total hours logged) and foster placement data — both critical for reports to donors and government bodies.

## Acceptance Criteria
- [x] Impact report service covers: animals served, adoptions, donations (by currency/method), in-kind donations, fund allocation, avg-time-to-adoption, cost-per-adoption
- [ ] Service extended with: active volunteer count, total volunteer hours logged, active foster placement count
- [ ] New metrics included in `generate_impact_report()` return dict
- [ ] Schema updated to include new sections
- [ ] API endpoint returns extended response
- [ ] All edge cases handled (empty state, errors, permissions)
- [ ] API endpoints documented in OpenAPI schema
- [ ] Unit and integration tests passing (≥80% coverage)

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files (service, schema, tests)
- [x] Change impact ≤10 lines of actual code
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple Fix — extending existing service with 2 additional queries

## Approach
1. Add `count_active_volunteers()` and `count_active_foster_placements()` to `impact_report_service.py`
2. Integrate into `generate_impact_report()`
3. Add `VolunteerSummary` and `FosterSummary` Pydantic models to `schemas/impact_report.py`
4. Extend `ImpactReportResponse` with the new fields
5. Add unit tests for the new functions

## Dependencies
- Depends on: RAP-061 (merged, ✓)

## Risks
- Risk: FosterPlacement and VolunteerHoursLog table schemas may differ → Mitigation: Read models before querying
