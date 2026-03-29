# RAP-248 Plan

## Objective
Implement Paraguayan government reporting export formats so the shelter can generate SENACSA annual census reports in both JSON and CSV formats.

## Description
Part of EPIC-50: Paraguayan Legal Compliance. SENACSA (Servicio Nacional de Calidad y Salud Animal) requires annual census reports from registered animal shelters. This ticket adds admin endpoints to generate and export those reports.

## Acceptance Criteria
- [x] GET /admin/reports/government/annual-census returns JSON census report
- [x] GET /admin/reports/government/annual-census/export returns CSV suitable for SENACSA submission
- [x] Reports include intake counts, adoption outcomes, vaccination totals, species/status breakdowns
- [x] CSV uses UTF-8 with BOM for Excel compatibility
- [x] Admin-only; public access returns 401
- [x] Unit and integration tests passing

## Complexity Assessment
**Track**: Simple Fix — new service + two endpoints, ≤5 files affected.

## Approach
1. Service `government_report_service.py`: AnnualCensusReport dataclass, generate_annual_census(), render_annual_census_csv()
2. Router `admin_government_reports.py`: two admin endpoints under /admin/reports/government/
3. Register in app.py
4. Unit tests (23) + integration tests (15)
