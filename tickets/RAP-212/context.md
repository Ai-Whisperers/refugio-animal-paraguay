# RAP-212 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 04:42

## Current Focus
Refactoring vaccination_certificate_service.py to use BasePDFGenerator and ShelterPDF.

## Technical State
- `src/services/vaccination_certificate_service.py` — existing service with standalone FPDF subclass
- `src/services/pdf_service.py` — base class from RAP-210 (ShelterPDF, BasePDFGenerator)
- `tests/unit/test_vaccination_certificate_service.py` — 278 lines, 32 tests, all passing
- API endpoint in `src/api/vaccinations.py` — calls `generate_vaccination_certificate()` directly

## Next Steps
1. Refactor vaccination_certificate_service.py to use BasePDFGenerator
2. Verify all tests still pass
3. Commit and push

## Blockers
None

## Key Decisions Made
- Keep backward-compat `generate_vaccination_certificate()` function
- Use `ShelterPDF` for header/footer (title: "CERTIFICADO DE VACUNACION")
- Add `VaccinationCertificateGenerator(BasePDFGenerator)` class
