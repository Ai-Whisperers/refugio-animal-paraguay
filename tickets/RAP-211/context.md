# RAP-211 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 00:00

## Current Focus
Adding generate_bytes() to ContractPDFGenerator and download endpoint to adoption_requests API.

## Technical State
- contract_service.py has generate() (file-based) only
- adoption_requests.py has POST /{id}/contract (generate) but no GET /{id}/contract/download
- donation_receipt_service.py already has generate_bytes() as reference pattern

## Next Steps
1. Add generate_bytes() to ContractPDFGenerator
2. Add download endpoint
3. Tests

## Blockers
None

## Key Decisions Made
- Using StreamingResponse (same as donation receipt endpoint pattern)
- Only staff can download contracts (same auth as generate)
