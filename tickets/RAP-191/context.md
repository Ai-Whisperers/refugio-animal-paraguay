# RAP-191 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-28

## Current Focus
Implementing the foster placement matching algorithm — backend only (V7, Sprint 4, EPIC-39 S2).

## Technical State
- FosterProfile model exists at src/db/models/foster_profile.py (RAP-190)
- Animal model exists at src/db/models/animal.py with species, size, status fields
- SmartMatchingService pattern at src/services/smart_matching_service.py — follow this pattern
- No foster_placements table yet — need migration 076

## Next Steps
1. Create FosterPlacement model + migration
2. Create foster_placement_service.py
3. Add API endpoints to foster.py
4. Write unit and integration tests

## Blockers
None

## Key Decisions Made
- FosterPlacement model: minimal (id, foster_profile_id, animal_id, started_at, ended_at)
- Scoring factors: species preference (20pts), home suitability (15pts), capacity (20pts), experience (5pts)
- Capacity check: if currently at max_animals, score = 0 (ineligible)

## RESUME POINT
Not paused.
