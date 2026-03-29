# RAP-246 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:35

## Current Focus
Adding GET /legal/adoption-contract to legal_documents.py router.

## Technical State
- No DB changes needed — template is static JSON
- Adding to src/api/legal_documents.py (already has /dpa endpoint)
- Supporting ?lang=es|en query param
- Tests: tests/unit/test_legal_documents.py, tests/integration/test_legal_documents.py

## Next Steps
1. Add adoption contract endpoint to legal_documents.py
2. Write unit and integration tests

## Blockers
None
