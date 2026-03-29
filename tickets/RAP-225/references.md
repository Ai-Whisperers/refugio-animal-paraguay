# RAP-225 References

## Key Files
- `src/services/gdpr_deletion_service.py` — main service (anonymize_volunteer, anonymize_rescuer, anonymize_foster added)
- `src/schemas/gdpr_deletion.py` — GDPRDeletionRequest / GDPRDeletionResponse extended
- `src/api/gdpr.py` — router updated to pass new optional IDs
- `src/db/models/volunteer.py` — VolunteerProfile model
- `src/db/models/rescuer.py` — RescuerProfile model (unique slug constraint)
- `src/db/models/foster.py` — FosterProfile model
- `tests/unit/test_gdpr_deletion_service.py` — unit tests
- `tests/integration/test_gdpr_deletion.py` — integration tests

## PR
- PR #350: feature/RAP-225-gdpr-extended-entity-anonymization → develop

## Epic
- EPIC-46-gdpr-right-to-erasure/stories/S1-data-deletion-api-with-anonymization/STORY.md
