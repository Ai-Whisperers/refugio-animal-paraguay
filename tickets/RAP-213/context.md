# RAP-213 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 04:42

## Current Focus
Refactoring DonationReceiptGenerator and TaxReceiptEUGenerator to use BasePDFGenerator.

## Technical State
- `src/services/donation_receipt_service.py` — DonationReceiptGenerator uses raw FPDF
- `src/services/tax_receipt_eu_service.py` — TaxReceiptEUGenerator uses raw FPDF
- `src/services/pdf_service.py` — BasePDFGenerator, ShelterPDF available
- Tests: 252+157=409 lines of unit tests, all currently passing

## Next Steps
1. Refactor donation_receipt_service.py
2. Refactor tax_receipt_eu_service.py
3. Add new tests for BasePDFGenerator interface
4. Verify all tests pass

## Blockers
None

## Key Decisions Made
- Use ShelterPDF for both receipt types (consistent header/footer)
- EU receipt keeps its ANBI notice box (rendered in _build_pdf after standard header)
- Keep all existing method signatures for backward compatibility
