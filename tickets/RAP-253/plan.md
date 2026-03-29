# RAP-253 Plan

## Objective
Implement capacity alerts and configurable thresholds as a backend endpoint that evaluates current occupancy against defined warning/critical levels and returns actionable alerts.

## Description
Add GET /api/admin/operational-dashboard/alerts endpoint that evaluates current shelter metrics against configurable warning (70%) and critical (85%) thresholds. Returns structured alerts with severity, message, and recommended actions.

## Acceptance Criteria
- [ ] GET /api/admin/operational-dashboard/alerts returns alerts based on live metrics
- [ ] Warning alert at >= 70% occupancy
- [ ] Critical alert at >= 85% occupancy
- [ ] Alert includes: severity, title, message, recommended_action
- [ ] Threshold values configurable via query params (warning_pct, critical_pct)
- [ ] Unit tests with 80%+ coverage

## Complexity Assessment
**Track**: Simple Fix — extends existing operational dashboard router

## Approach
1. Add _evaluate_capacity_alerts() to operational_metrics_service.py
2. Add CapacityAlert schema and GET /alerts endpoint to operational_dashboard.py
3. Write unit tests

## Dependencies
- Depends on: RAP-250 (operational metrics service)
