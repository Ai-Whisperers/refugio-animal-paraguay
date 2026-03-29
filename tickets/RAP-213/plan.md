# RAP-213 Plan

## Objective
Refactor the donation receipt PDF services (`DonationReceiptGenerator` and `TaxReceiptEUGenerator`) to use `BasePDFGenerator` and `ShelterPDF`, ensuring consistent shelter branding and a unified PDF generation API.

## Description
EPIC-43 S1 (RAP-210) established `BasePDFGenerator` and `ShelterPDF`. Both donation receipt services were written before this base existed and use standalone `FPDF` instances. This ticket refactors them to use the base class, making the `generate_bytes()` signature consistent with all other generators.

## Acceptance Criteria
- [ ] `DonationReceiptGenerator` extends `BasePDFGenerator` and uses `ShelterPDF`
- [ ] `TaxReceiptEUGenerator` extends `BasePDFGenerator` (keeps bilingual EU content)
- [ ] Both use `ShelterPDF` for consistent branded header/footer
- [ ] Existing API endpoints unchanged (backward compatible)
- [ ] Unit tests pass with the new class hierarchy
- [ ] ruff and black clean

## Complexity Assessment
**Track**: Simple Fix — refactoring existing classes to extend BasePDFGenerator

## Approach
1. `DonationReceiptGenerator`: extend `BasePDFGenerator`, use `ShelterPDF(title="RECIBO DE DONACION")`
2. `TaxReceiptEUGenerator`: extend `BasePDFGenerator`, use `ShelterPDF(title="DONATION TAX RECEIPT / KWITANTIE BELASTINGAFTREK")`, keep ANBI notice
3. Add `generate_bytes()` type annotation update (inherited from BasePDFGenerator)
4. Keep all existing public interfaces unchanged

## Dependencies
- Depends on: RAP-210 (pdf_service.py BasePDFGenerator) — DONE (PR #335)

## Risks
- Risk: EU receipt rendering changes — Mitigation: unit test verifies PDF starts with %PDF and has correct size
