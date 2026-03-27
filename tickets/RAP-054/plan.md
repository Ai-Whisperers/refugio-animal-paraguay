# RAP-054 Plan

## Objective
Generate PDF adoption contracts for approved adoption requests with Spanish-language content.

## Description
Shelter staff need to produce formal adoption contracts as PDFs when an adoption request is approved. The contract includes adopter details, animal details, commitment clauses in Spanish, and signature blocks. This supports the Paraguayan legal context for animal adoption documentation.

## Acceptance Criteria
- [x] Alembic migration adds contract_pdf_path and contract_generated_at to adoption_requests
- [x] ContractData dataclass captures all required contract fields
- [x] ContractPDFGenerator produces valid PDF files with Spanish content
- [x] POST /adoption-requests/{id}/contract endpoint generates and stores contract
- [x] Endpoint returns 422 for non-approved requests, 404 for nonexistent
- [x] Regeneration overwrites existing contract at same path
- [x] Contract fields stored on adoption_request row and returned in responses
- [x] Unit tests for service layer (ContractData, generator, clauses)
- [x] Integration tests for endpoint (201, 404, 422, overwrite, storage)

## Complexity Assessment
**Track**: Complex Implementation

- Multiple files affected (migration, model, service, schema, router, tests)
- New service with PDF generation dependency (fpdf2)
- Cross-layer changes (DB → ORM → service → API → schema)

**Assessment result**: Complex — 5+ files, new service layer, PDF generation

## Approach
1. Add Alembic migration for contract columns
2. Implement ContractPDFGenerator service with Spanish template
3. Add API endpoint with staff-only auth
4. Write comprehensive unit and integration tests

## Dependencies
- Depends on: fpdf2 (already installed), approved adoption request workflow (RAP-006)
