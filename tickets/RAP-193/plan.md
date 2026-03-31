# RAP-193 Plan

## Objective
Implement a foster-to-adopt conversion workflow allowing staff to convert an active foster placement into a formal adoption request.

## Description
When a foster family decides to adopt the animal they're fostering, staff need a streamlined workflow to convert the foster placement into an adoption. This eliminates redundant data entry and maintains a clear record of the foster-to-adopt transition. The conversion closes the foster placement, creates a pre-approved adoption request, and updates the animal's status to ADOPTED.

## Acceptance Criteria
- [ ] POST /api/staff/foster/placements/{id}/convert-to-adoption endpoint converts an active placement to an adoption request
- [ ] Conversion closes the foster placement (sets ended_at)
- [ ] Animal status updated to ADOPTED
- [ ] Adoption request created with status APPROVED (fast-track, staff initiated)
- [ ] Returns 404 for unknown placement
- [ ] Returns 422 if placement is already closed (ended_at is not null)
- [ ] Returns 422 if no adopter record exists for the foster family user
- [ ] Unit tests for conversion service logic
- [ ] Integration tests for the endpoint

## Complexity Assessment
**Track**: Complex — multiple models updated atomically

**Assessment result**: Complex — touches FosterPlacement, Animal, AdoptionRequest in one transaction

## Approach
1. Add `convert_foster_to_adoption` service function in `foster_placement_service.py`
2. Add migration for tracking conversion metadata on foster_placements table (optional — can use notes)
3. Add endpoint in `foster.py` staff_router
4. Write unit and integration tests

## Dependencies
- Depends on: RAP-191 (FosterPlacement model), RAP-190 (FosterProfile), RAP-006 (AdoptionRequest)

## Risks
- Risk: Adopter record may not exist if user hasn't created one → Mitigation: clear 422 error with message
