# RAP-642 Plan

## Objective
Build onboarding checklist and training status tracking for volunteers.

## Description
S3 of EPIC-36. Staff define onboarding checklist items; volunteers complete them.
System tracks training status per volunteer. Approved volunteers see their outstanding
onboarding tasks.

## Acceptance Criteria
- [ ] VolunteerOnboardingItem model: id, volunteer_id (FK), item_key (string), title, completed (bool), completed_at, completed_by (staff user_id), notes
- [ ] PREDEFINED_ONBOARDING_ITEMS constant: orientation, safety_training, animal_handling, first_aid, shelter_rules
- [ ] POST /api/staff/volunteers/{id}/onboarding endpoint: create/initialize onboarding checklist for a volunteer
- [ ] GET /api/volunteers/onboarding endpoint: get current user's onboarding checklist
- [ ] PUT /api/staff/volunteers/{id}/onboarding/{item_key} endpoint: mark item complete/incomplete (staff only)
- [ ] onboarding_complete boolean property on profile (True when all mandatory items done)
- [ ] Migration 073 for volunteer_onboarding_items table
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests: initialize checklist, complete item, get status

## Complexity Assessment
**Assessment result**: Simple — new table, ~3 endpoints, clear scope

## Approach
1. Create VolunteerOnboardingItem model + predefined items constant
2. Migration 073
3. Add staff endpoint to initialize checklist
4. Add staff endpoint to mark items
5. Add volunteer endpoint to GET their checklist
6. Frontend: simple checklist component on /volunteer/profile or a new /volunteer/onboarding page
7. Tests

## Dependencies
- Depends on: RAP-640 (volunteer_profiles table), RAP-641 (profile page pattern)

## Risks
None significant
