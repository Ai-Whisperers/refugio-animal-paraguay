# RAP-225 Plan

## Objective
Extend the GDPR data deletion API to cover all PII-bearing entities (volunteers, rescuers, foster profiles, users with phone/full_name) and add deletion request tracking.

## Description
The existing deletion service only anonymizes donors and adopters. GDPR Article 17 requires all personal data to be erased across all systems. This story extends the anonymization to cover volunteer profiles, rescuer profiles, foster profiles, and adds a `DeletionRequest` model for audit/tracking purposes. A new endpoint to list pending requests supports the admin review workflow.

## Acceptance Criteria
- [ ] All PII-bearing entities are anonymized: donor, adopter, volunteer, rescuer, foster, user (full_name, phone)
- [ ] A `DeletionRequest` model records each request with requestor, target user, status, and timestamp
- [ ] POST /gdpr/deletion-request creates a DeletionRequest record before executing
- [ ] GET /gdpr/deletion-requests returns paginated list of deletion requests (admin only)
- [ ] API endpoints documented in OpenAPI schema
- [ ] Unit and integration tests passing (80%+ coverage)

## Complexity Assessment
**Track**: Complex Implementation

### Assessment result: Complex — affects 5+ models, requires DB migration, new endpoints, extended service logic

## Approach
1. Add `DeletionRequest` DB model + Alembic migration
2. Extend `gdpr_deletion_service.py` to anonymize volunteer, rescuer, and foster profiles
3. Update `GDPRDeletionRequest` schema to accept `volunteer_id`, `rescuer_id`, `foster_id`
4. Update `GDPRDeletionResponse` schema with new fields
5. Add `GET /gdpr/deletion-requests` endpoint
6. Write unit tests for new service functions
7. Write integration tests for new endpoint

## Dependencies
- Depends on: existing GDPR deletion service (RAP-007 era)
- Depends on: VolunteerProfile, RescuerProfile, FosterProfile models (already exist)

## Risks
- Risk: migration ordering conflicts → Mitigation: use next available migration number
