# RAP-248 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 16:00

## Technical State
- Service: `src/services/government_report_service.py` — AnnualCensusReport dataclass, SpeciesBreakdown, StatusBreakdown, generate_annual_census(), render_annual_census_csv()
- Router: `src/api/admin_government_reports.py` — GET /admin/reports/government/annual-census (JSON), GET /admin/reports/government/annual-census/export (CSV)
- Registered in `src/app.py`
- Unit tests: `tests/unit/test_government_report_service.py` (23 tests)
- Integration tests: `tests/integration/test_government_reporting.py` (15 tests)

## Key Decisions Made
- year param defaults to current calendar year, bounded [2000, 2100]
- CSV uses UTF-8 BOM for Excel compatibility (Paraguay standard)
- Bilingual CSV headers (Spanish for SENACSA, English species/status codes kept for traceability)
