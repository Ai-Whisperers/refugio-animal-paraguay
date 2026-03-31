# RAP-250 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 16:42

## Current Focus
Building operational dashboard API with real DB queries

## Technical State
- Animal model has status (intake/quarantine/available/foster/under_treatment/adopted/deceased)
- Animal model has created_at timestamp for LOS calculations
- Executive dashboard at /api/admin/dashboard/ uses hardcoded data
- New endpoint: /api/admin/operational-dashboard/metrics
- New service: src/services/operational_metrics_service.py

## Next Steps
1. Create service with aggregate queries
2. Create router
3. Register in app.py
4. Write tests

## Blockers
None

## Key Decisions Made
- Use separate router/service from executive_kpi_dashboard to keep concerns separated
- Capacity is configurable via environment variable with default of 200
