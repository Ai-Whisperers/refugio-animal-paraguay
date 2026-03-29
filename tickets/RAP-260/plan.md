# RAP-260 Plan

## Objective
Create an AdoptionOutcome model and API to track high-level adoption outcomes (successful, returned, rehomed, deceased) aggregated from follow-up and return data.

## Description
EPIC-53 requires a dedicated outcome record per adoption that captures the final status at the adoption level (beyond individual follow-up checkpoints). This enables success rate analytics, return rate reporting, and trend dashboards.

## Acceptance Criteria
- [ ] AdoptionOutcome SQLAlchemy model created with outcome_type, date, notes, aggregated scores
- [ ] Alembic migration 091 creates adoption_outcomes table
- [ ] Service layer: create, get, list, aggregate outcome stats
- [ ] API: POST/GET/PUT endpoints for outcomes, GET analytics endpoint
- [ ] Unit tests with 80%+ coverage
- [ ] Registered in app.py

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new model + migration + service + API + tests

## Approach
1. Create AdoptionOutcomeType StrEnum and AdoptionOutcome model
2. Write migration 091
3. Write adoption_outcome_service.py with CRUD + analytics
4. Write adoption_outcomes.py router
5. Register router in app.py
6. Write unit tests

## Dependencies
- Depends on: AdoptionRequest model (existing), FollowUp model (existing)
