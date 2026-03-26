# RAP-035 Plan

## Objective
Implement GDPR consent tracking system with database model, API endpoints, consent validation service, and audit integration.

## Description
EU donors require explicit consent management per GDPR Article 7. This ticket builds the backend infrastructure: a consent records table, CRUD API for managing user communication preferences, a validation service that checks consent before sending communications, and audit logging for all consent changes.

## Acceptance Criteria
- [x] user_consents table with: user_id, consent_type, status, opt_in_date, opt_out_date, ip_address, user_agent, method, notes
- [x] Consent type enum: marketing_email, newsletter, sms_updates, event_invitations, donation_receipts
- [x] PUT /users/{user_id}/consents endpoint for managing preferences
- [x] GET /users/{user_id}/consents endpoint for viewing current consent status
- [x] GET /users/{user_id}/consents/history endpoint for consent change log
- [x] Consent validation service (check_consent) for pre-send verification
- [x] Audit events published for consent changes
- [x] Idempotent: re-granting active consent is a no-op
- [x] Unit tests for consent service and validation logic
- [x] Integration tests for consent API endpoints

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new model with migration, 3 API endpoints, validation service, audit integration, enums, tests across unit and integration.

## Approach
1. Create UserConsent model + ConsentType/ConsentMethod/ConsentStatus enums
2. Create Alembic migration for user_consents table
3. Create consent Pydantic schemas
4. Create consent API router with GET/PUT endpoints
5. Create consent validation service
6. Wire audit events for consent changes
7. Register router in app.py
8. Write unit + integration tests

## Dependencies
- Depends on: Audit Trail System (V2 #2) — DONE (PR #15)
- Depends on: JWT Auth (RAP-007) — DONE
- Blocks: GDPR Data Export (V2 #13)

## Risks
- Risk: Schema evolution if new consent types needed later → Mitigation: Enum-based consent types, easy to extend
