---
story: S2
epic: EPIC-78
ticket: RAP-518
title: "Pre-qualification questionnaire API"
status: ready
points: 5
priority: P0
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S2: Pre-qualification questionnaire API

## Story
As a **backend system**, I want **to score adopter answers against animal requirements** so that **we can determine if adopter is qualified**.

## Description
Implement scoring engine that evaluates adopter answers against requirements, returns qualification status and suggested animals.

## Acceptance Criteria
- [ ] POST /adoption/pre-qualify endpoint: accepts JSON body with: animal_id (UUID), answers (object with key-value pairs matching question IDs)
- [ ] Scoring engine: for each requirement in animal's requirements list:
  - If mandatory and answer doesn't meet requirement: overall_qualified = false, add to failed_requirements list
  - If preferred and answer meets: add to score (+10 points per preferred met)
  - If mandatory and answer meets: add to score (+5 points per mandatory met)
- [ ] Response format: {qualified: bool, score: 0-100, failed_requirements: [{type, message, is_mandatory}], suggested_animals: [{id, name, species, photo_url, match_score}], estimated_wait_time: string}
- [ ] Qualification logic: qualified = true if all mandatory requirements met, false otherwise
- [ ] Score calculation: (met_requirements_count / total_requirements_count) * 100, bounded 0-100
- [ ] Failed requirements message: human-readable explanation, e.g. "Property must have a yard but your answer was 'apartment'"
- [ ] Suggested animals: GET /adoption/match?adopter_profile=... returns top 5-10 animals that match adopter's profile (use smart matching from S6)
- [ ] Suggested animals should be: available for adoption, match adopter's experience level, match home type preferences, match other pets compatibility
- [ ] Estimated wait time: based on application queue depth for qualified animals, e.g. "3-4 weeks"
- [ ] Rate limiting: max 1 qualification per IP per animal per day (prevent gaming)
- [ ] Logging: log all pre-qualification attempts for analytics
- [ ] Error handling: invalid animal_id returns 404, invalid answers return 400 with details of which questions had invalid answers

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test scoring logic, requirement matching, suggested animals
- [ ] Integration test: fully qualified adopter returns qualified=true and high score
- [ ] Integration test: unqualified adopter (failed mandatory) returns qualified=false
- [ ] Integration test: partially qualified adopter (met some preferred) returns correct score
- [ ] Integration test: suggested animals are relevant
- [ ] Integration test: rate limiting enforced
- [ ] Manual testing: verify scoring accuracy with various answer combinations
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoint /adoption/pre-qualify, complex scoring logic
- Scoring algorithm: iterate requirements, check answer against requirement.value, accumulate score
- Requirement matching: for each requirement type, implement specific matching logic
- Suggested animals: call GET /adoption/match with adopter profile, limit 10 results
- Rate limiting: Redis key pattern "prequal:{ip}:{animal_id}:{date}", max 1 per day
- Logging: log with animal_id, adopter IP, score, qualified status
- Performance: pre-qualification should be fast (<1s), optimize queries
- Invalid answers: check each answer against expected type/format for requirement

## Story Points: 5
