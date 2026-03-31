# RAP-254 Plan

## Objective
Add CSV export endpoints to the operational dashboard so staff can download metrics snapshots for external reporting.

## Description
Add two export endpoints:
1. GET /api/admin/operational-dashboard/export/metrics — exports the current metrics snapshot as CSV
2. GET /api/admin/operational-dashboard/export/population — exports population breakdown as CSV

## Acceptance Criteria
- [ ] GET /api/admin/operational-dashboard/export/metrics returns a CSV file download
- [ ] CSV contains all metric fields from the /metrics endpoint
- [ ] GET /api/admin/operational-dashboard/export/population returns population breakdown CSV
- [ ] Both endpoints accept period_days and capacity query params
- [ ] StreamingResponse pattern (consistent with existing donations/export)
- [ ] Requires staff auth
- [ ] Unit tests with 80%+ coverage

## Complexity Assessment
**Track**: Simple Fix — extends existing operational dashboard router with well-understood pattern

## Approach
1. Add CSV export functions to operational_metrics_service.py
2. Add export endpoints to operational_dashboard.py
3. Write unit tests

## Dependencies
- Depends on: RAP-250 (operational metrics service)
