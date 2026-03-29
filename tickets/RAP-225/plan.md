# RAP-225 Plan

## Objective
Extend the GDPR data deletion service to anonymize volunteer, rescuer, and foster profiles, ensuring EPIC-46 S1 covers all personally-linked entities.

## Description
The existing deletion service handled donors, adopters, and user accounts. This ticket extends it to also anonymize VolunteerProfile, RescuerProfile, and FosterProfile personal data — completing the Article 17 coverage for all entities that carry PII.

## Acceptance Criteria
- [x] `anonymize_volunteer()` clears emergency contact name/phone, bio; sets motivation to "[DELETED]", status to "inactive"
- [x] `anonymize_rescuer()` clears display_name, sets unique anonymized slug, clears bio/location/social_links/phone_whatsapp
- [x] `anonymize_foster()` clears motivation/experience_description/other_pets_description; sets status to "inactive"
- [x] `deactivate_user_account()` also clears full_name and phone
- [x] `process_deletion_request()` accepts volunteer_id, rescuer_id, foster_id optional params
- [x] GDPRDeletionRequest and GDPRDeletionResponse schemas updated with new fields
- [x] Unit tests cover all new anonymization functions
- [x] Integration test verifies response includes new boolean fields
- [x] All quality gates pass (ruff, mypy, black, pytest)

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — touches 5+ files, adds 3 new service functions, extends schema and API layer.

## Approach
1. Extend gdpr_deletion_service.py with three new anonymize_* functions
2. Update deactivate_user_account() to also clear full_name and phone
3. Extend process_deletion_request() signature and summary dict
4. Update schemas (GDPRDeletionRequest, GDPRDeletionResponse)
5. Update API router docstring
6. Add unit tests (TestAnonymizeVolunteer, TestAnonymizeRescuer, TestAnonymizeFoster, TestDeactivateUserAccountExtended)
7. Update integration test

## Dependencies
- Depends on: RAP-224 (existing deletion service baseline)
- Blocks: RAP-226 (third-party cascade builds on this)

## Risks
- UNIQUE constraint on rescuer slug → Mitigation: _anonymized_slug() with uuid4 suffix
