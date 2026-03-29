# RAP-193 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-28 00:00

## Current Focus
Implementing foster-to-adopt conversion endpoint and service.

## Technical State
- FosterPlacement model: src/db/models/foster_placement.py
- FosterProfile model: src/db/models/foster_profile.py
- AdoptionRequest model: src/db/models/adoption_request.py
- Animal model: src/db/models/animal.py (AnimalStatus.ADOPTED)
- Foster API: src/api/foster.py
- Foster placement service: src/services/foster_placement_service.py

## Next Steps
1. Add convert_foster_to_adoption to foster_placement_service.py
2. Add POST endpoint to foster.py staff_router
3. Write unit tests in tests/unit/
4. Write integration tests in tests/integration/

## Blockers
None

## Key Decisions Made
- Adoption request created with status APPROVED (staff-initiated fast-track)
- Foster placement ended_at set to now() on conversion
- Animal status set to ADOPTED
- adopter_id resolved from the foster family's user_id → adopters table
