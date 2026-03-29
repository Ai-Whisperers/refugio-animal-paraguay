# RAP-266 Plan

## Objective
Create an impact report PDF template that renders a branded, printable impact report using the aggregated shelter metrics.

## Description
Donors, board members, and government bodies need a formatted PDF version of the impact report. This ticket implements the PDF generator using the existing BasePDFGenerator/ShelterPDF foundation, and exposes a new `/impact-reports/generate-pdf` endpoint that streams the PDF bytes.

## Acceptance Criteria
- [ ] `ImpactReportPDFGenerator` class implementing `BasePDFGenerator`
- [ ] PDF renders: metadata header, animals served table, adoptions table, donations breakdown, fund allocation table, performance metrics
- [ ] Endpoint `POST /impact-reports/generate-pdf` returns a PDF response with correct Content-Type
- [ ] Staff auth required on endpoint
- [ ] Unit tests for PDF generator (structure + content)
- [ ] Integration test for the endpoint

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files (new service, updated router, tests)
- [x] Low risk of side effects
- [x] Solution pattern is well-understood (follows existing BasePDFGenerator pattern)

**Assessment result**: Simple Fix — new file following existing pattern

## Approach
1. Create `src/services/impact_report_pdf_service.py` with `ImpactReportData` dataclass and `ImpactReportPDFGenerator`
2. Add `POST /impact-reports/generate-pdf` to `src/api/impact_reports.py`
3. Write unit tests

## Dependencies
- Depends on: RAP-061 (base service), RAP-265 (data aggregation — will merge soon)
