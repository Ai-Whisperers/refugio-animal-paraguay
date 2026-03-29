# RAP-214 Plan

## Objective
Complete the migration of ALL remaining PDF generators to `BasePDFGenerator` + `ShelterPDF`, ensuring every PDF document in the shelter platform uses consistent branded letterhead.

## Description
EPIC-43 S3 (RAP-212) and S4 (RAP-213) refactored the vaccination cert and donation receipt services. S5 completes the migration by refactoring the remaining 3 services: `contract_service.py`, `anbi_compliance_service.py`, and `annual_donation_summary_service.py`.

## Acceptance Criteria
- [ ] `ContractPDFGenerator` extends `BasePDFGenerator`, uses `ShelterPDF`
- [ ] `ANBIDocumentGenerator` extends `BasePDFGenerator`, uses `ShelterPDF`
- [ ] `AnnualSummaryGenerator` extends `BasePDFGenerator`, uses `ShelterPDF`
- [ ] All existing tests pass unchanged
- [ ] ruff and black clean

## Complexity Assessment
**Track**: Complex — affects 3 services, each ~200-300 lines

## Approach
For each service:
1. Replace `from fpdf import FPDF` with `from src.services.pdf_service import BasePDFGenerator, ShelterPDF`
2. Extend `BasePDFGenerator` instead of plain object
3. Replace `FPDF()` with `ShelterPDF(title=...)` in `_build_pdf()`
4. Use `pdf.section_title()` and `pdf.info_row()` helpers where applicable
5. Remove duplicate `generate_bytes()` if it matches base class signature

## Dependencies
- RAP-210: pdf_service.py — DONE (PR #335)

## Risks
- Risk: ShelterPDF header changes visual output → Mitigation: unit tests verify PDF bytes are valid
