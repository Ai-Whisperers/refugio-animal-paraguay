# RAP-246 Plan

## Objective
Add a GET /legal/adoption-contract endpoint that returns the Paraguayan legal adoption contract template, including all required clauses under Ley 4840/2013 and Ley 3140/2006.

## Description
Paraguay's animal welfare laws require a signed adoption contract for every animal transfer. This template endpoint returns a structured document that shelter staff can use to generate printed/PDF contracts. The template includes all legally required clauses.

## Acceptance Criteria
- [ ] GET /legal/adoption-contract returns 200 with the contract template
- [ ] Template includes: animal description, adopter identification, vaccination clause, sterilization clause, return policy, home inspection clause, prohibition on resale, cruelty prohibition, microchip acknowledgment
- [ ] Template includes legal basis (Ley 4840/2013, Ley 3140/2006)
- [ ] Template includes signature fields for adopter and shelter representative
- [ ] Template supports optional language parameter (es default, en available)
- [ ] Unit tests for endpoint response structure
- [ ] Integration tests for happy path and language variation

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — adding a GET endpoint to existing legal_documents.py router. No DB changes needed. Template is structured JSON.

## Approach
1. Add GET /legal/adoption-contract to src/api/legal_documents.py
2. Support `?lang=es|en` query parameter (default: es)
3. Return bilingual-aware structured contract template
4. Write unit tests and integration tests

## Dependencies
- Depends on: none (self-contained template endpoint)
