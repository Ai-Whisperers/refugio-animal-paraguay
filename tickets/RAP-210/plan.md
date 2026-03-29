# RAP-210 Plan

## Objective
Create a centralized base PDF generation service using fpdf2 that provides common shelter branding, shared utilities, and a consistent foundation for all PDF documents in the system.

## Description
The project already has multiple individual PDF services (contract_service, donation_receipt_service, vaccination_certificate_service, etc.) that each duplicate shelter constants and helper methods. This story creates a shared base (`pdf_service.py`) with a `ShelterPDF` FPDF subclass and `BasePDFGenerator` abstract class. Future PDF services extend this base instead of duplicating code.

## Acceptance Criteria
- [ ] `src/services/pdf_service.py` created with: `SHELTER_INFO` dict, `ShelterPDF(FPDF)` subclass with header/footer, `BasePDFGenerator` abstract base class with `generate_bytes()` and `generate_file()`, `PDFGenerationError` exception
- [ ] All edge cases handled (empty data, I/O errors)
- [ ] Unit tests with 80%+ coverage
- [ ] ruff/black clean

## Complexity Assessment
**Track**: Simple Fix — adds a new module, no existing code broken

**Assessment result**: Simple Fix — new file, well-understood patterns

## Approach
1. Create `src/services/pdf_service.py` with base classes
2. Write comprehensive unit tests
3. Quality gate check

## Dependencies
- Depends on: fpdf2 (already in pyproject.toml)
- Blocks: RAP-211 (adoption contract uses base)

## Risks
- Risk: Breaking existing PDF services → Mitigation: Base class is additive only, existing services unchanged
