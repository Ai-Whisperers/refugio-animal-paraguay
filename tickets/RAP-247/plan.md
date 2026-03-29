# RAP-247 Plan

## Objective
Implement Paraguayan record retention policy as an API endpoint and admin status check, so the shelter can demonstrate legal compliance with mandatory retention periods.

## Description
Part of EPIC-50: Paraguayan Legal Compliance. Paraguay law mandates minimum retention periods for animal shelter records under Ley 4840/2013, Ley 3140/2006, Codigo Civil Art. 633, and Ley 125/91. This ticket exposes the policy publicly and provides an admin endpoint for live record counts.

## Acceptance Criteria
- [x] GET /legal/record-retention-policy returns 200 with full retention policy
- [x] Policy includes all mandatory record types with legal basis citations
- [x] GET /admin/data-retention/paraguayan-status returns live DB counts (admin-only)
- [x] API endpoints documented in OpenAPI schema (FastAPI auto-generates)
- [x] Unit and integration tests passing

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — new service + two endpoints, ≤5 files affected, well-understood pattern.

## Approach
1. Service file `paraguayan_retention_service.py` with constants, policy list, `get_retention_status()` async function
2. Public endpoint `GET /legal/record-retention-policy` in `legal_documents.py`
3. Admin endpoint `GET /admin/data-retention/paraguayan-status` in `admin_data_retention.py`
4. Unit tests (44) + integration tests (13)

## Dependencies
- Depends on: existing Animal, AdoptionRequest, Donation models
- Blocked by: nothing
