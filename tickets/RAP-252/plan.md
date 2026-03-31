# RAP-252 Plan

## Objective
Add trend charts (daily/weekly/monthly) to the operational dashboard by extending the backend with a `/trends` endpoint and creating a frontend trend charts page.

## Description
Extend the operational dashboard API with `GET /api/admin/operational-dashboard/trends` that returns time-series intake/outcome data. Implement frontend page `/admin/operational-dashboard/trends` with recharts AreaChart/LineChart visualizations.

## Acceptance Criteria
- [ ] Backend: GET /api/admin/operational-dashboard/trends returns grouped time-series data
- [ ] Supports grouping by: daily, weekly, monthly
- [ ] Each data point includes: period_label, intake_count, outcome_count
- [ ] Frontend: trend charts page at /admin/operational-dashboard/trends
- [ ] Charts show intake vs outcome trends over time
- [ ] Toggle between daily/weekly/monthly views
- [ ] Unit tests for backend service (80%+ coverage)
- [ ] Vitest unit tests for frontend chart component

## Complexity Assessment
**Track**: Complex — new backend endpoint + new frontend page

## Approach
1. Add trends query to operational_metrics_service.py
2. Add /trends endpoint to operational_dashboard.py router
3. Create frontend trends page with recharts AreaChart
4. Write tests for both backend and frontend

## Dependencies
- Depends on: RAP-250 (metrics API), RAP-251 (KPI cards page structure)

## Risks
- Risk: Historical data approximation — SQLAlchemy uses created_at as proxy for intake events → Mitigation: document this limitation, use same approach as existing intake_outcome API
