# RAP-269 References

## New Files
- `src/services/scheduled_report_service.py` — Core scheduled report service
- `src/api/scheduled_reports.py` — FastAPI router (trigger + config endpoints)
- `tests/unit/test_scheduled_report_service.py` — 30 unit tests

## Modified Files
- `src/app.py` — Added `scheduled_reports_router` registration
- `src/services/annual_report.py` — Added `generate_annual_report_from_db()` (cross-branch dependency workaround)

## Related
- RAP-265: `src/services/impact_report_service.py` — `generate_impact_report()` used by monthly builder
- RAP-266: `src/services/impact_report_pdf_service.py` — `ImpactReportPDFGenerator` used by monthly builder
- RAP-268: `src/services/annual_report.py` — `generate_annual_report_from_db()` origin (will deduplicate on merge)

## Branch
`feature/RAP-269-scheduled-report-generation`

## PR
Pushed — manual creation needed at:
https://github.com/Ai-Whisperers/refugio-animal-paraguay/pull/new/feature/RAP-269-scheduled-report-generation
