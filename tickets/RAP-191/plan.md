# RAP-191 Plan

## Objective
Implement a foster placement matching algorithm that scores and ranks approved foster families against animals needing fostering, enabling staff to quickly identify the best family for each animal.

## Description
Foster families have preferences (animal types, home environment, capacity) recorded during registration (RAP-190). This ticket adds the matching logic: a service that scores foster families against a given animal's needs, and API endpoints for staff to retrieve ranked recommendations.

## Acceptance Criteria
- [ ] Foster placement model tracks active placements (animal ↔ foster family)
- [ ] Matching service scores foster families for a given animal using: preferred_animal_types, home environment, current capacity
- [ ] Staff endpoint: GET /api/staff/foster/match/{animal_id} returns ranked foster families
- [ ] Staff endpoint: GET /api/staff/foster/{profile_id}/matches returns compatible animals for a foster family
- [ ] Unit tests cover scoring logic (all branches: species match, capacity, home type bonuses)
- [ ] Integration tests cover the API endpoints
- [ ] OpenAPI schema is complete

## Complexity Assessment
**Track**: Complex Implementation

- Multiple files: model, migration, service, API update, tests
- Scoring algorithm with several factors
- Requires DB query for current placement counts

**Assessment result**: Complex — 3 new files + 2 updated files, new migration, algorithm logic

## Approach
1. Create `FosterPlacement` model + migration (links foster_profile ↔ animal, tracks start/end)
2. Create `foster_placement_service.py` with scoring and matching functions
3. Add 2 staff endpoints to `foster.py`
4. Unit tests for service; integration tests for endpoints

## Dependencies
- Depends on: RAP-190 (FosterProfile model) — DONE

## Risks
- Risk: foster_placements table adds complexity → Mitigation: keep model minimal for now
