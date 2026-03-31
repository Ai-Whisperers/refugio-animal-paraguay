# RAP-212 Plan

## Objective
Refactor the vaccination certificate PDF service to use the centralized `BasePDFGenerator` and `ShelterPDF` from `pdf_service.py`, ensuring consistent branded headers/footers across all PDF documents.

## Description
EPIC-43 S1 (RAP-210) established a centralized `BasePDFGenerator` abstract class and `ShelterPDF` FPDF subclass. The existing `vaccination_certificate_service.py` was written before that base class existed and uses its own standalone `VaccinationCertificatePDF(FPDF)` with a custom header/footer. This ticket refactors it to:
1. Replace the standalone FPDF subclass with `ShelterPDF` for consistent branding
2. Introduce a `VaccinationCertificateGenerator` that extends `BasePDFGenerator`
3. Keep backward compatibility (existing API endpoint unchanged)
4. Add unit tests covering the `BasePDFGenerator` interface

## Acceptance Criteria
- [ ] `VaccinationCertificateGenerator` extends `BasePDFGenerator`
- [ ] `_build_pdf()` returns a `ShelterPDF` instance with consistent branded header/footer
- [ ] `generate_bytes()` works (inherited from `BasePDFGenerator`)
- [ ] Backward compat: existing `generate_vaccination_certificate()` helper still works
- [ ] API endpoint `/animals/{animal_id}/vaccination-certificate` still works
- [ ] Unit tests covering generator (empty vaccinations, multiple vaccinations, error case)
- [ ] All unit tests pass, ruff/black clean

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified — standalone PDF class not using base
- [x] Solution affects ≤3 files — vaccination_certificate_service.py + test file
- [x] Change impact ≤10 lines of actual code — mostly class inheritance change
- [x] Low risk of side effects — same API, same output format
- [x] Solution pattern is well-understood — follow contract_service.py pattern

**Assessment result**: Simple Fix — refactoring existing class to extend BasePDFGenerator

## Approach
1. Import `BasePDFGenerator`, `ShelterPDF`, `PDFGenerationError` from `pdf_service.py`
2. Replace `VaccinationCertificatePDF(FPDF)` with `ShelterPDF` usage
3. Add `VaccinationCertificateGenerator(BasePDFGenerator)` implementing `_build_pdf()`
4. Keep `generate_vaccination_certificate()` as a backward-compat wrapper
5. Add unit tests for the new generator class

## Dependencies
- Depends on: RAP-210 (pdf_service.py BasePDFGenerator) — DONE (PR #335)

## Risks
- Risk: Branding change in header (ShelterPDF vs old inline header) → Mitigation: unit test verifies PDF content is correct and contains expected text
