# RAP-233 Plan

## Objective
Provide a Data Processing Agreement (DPA) template via API endpoint for use with third-party processors.

## Acceptance Criteria
- [ ] GET /legal/dpa returns structured DPA template
- [ ] Template includes: subject matter, nature/purpose, data categories, obligations, sub-processors, security, breach notification, transfers, governing law
- [ ] Signature fields for Controller and Processor
- [ ] Contact email for execution
- [ ] 9 unit tests passing

## Complexity Assessment
**Track**: Simple Fix — new stateless GET endpoint returning structured data.
**Assessment result**: Simple Fix — no DB, no auth required (public document).

## Approach
1. Create src/api/legal_documents.py with GET /legal/dpa
2. Register router in app.py
3. Write unit tests (9 tests, 100% coverage)
