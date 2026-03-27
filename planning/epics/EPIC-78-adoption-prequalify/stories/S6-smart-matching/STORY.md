---
story: S6
epic: EPIC-78
ticket: RAP-522
title: "Smart matching algorithm"
status: ready
points: 5
priority: P1
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S6: Smart matching algorithm

## Story
As a **system**, I want **to match adopters with suitable animals** so that **we can increase adoption success rates**.

## Description
Implement smart matching algorithm that scores animals against adopter profile. Returns ranked list of best-fit animals.

## Acceptance Criteria
- [ ] GET /adoption/match?answers=... endpoint: accepts adopter answers (same format as pre-qualify answers), returns top 10 available animals sorted by match_score DESC
- [ ] Match scoring algorithm: for each available animal:
  - Get all adoption requirements for animal
  - For each requirement: check if adopter answer meets requirement
  - Calculate match score: (met_requirements / total_requirements) * 100
  - Apply preference bonuses: +5 points for preferred met, neutral for mandatory met
  - Apply species preference if data exists: +10 if adopter mentioned preference
  - Apply size preference if data exists: +5 if size matches
  - Experience level matching: +10 if adopter experience >= animal minimum experience
  - Final score: capped at 100, minimum 0
- [ ] Response format: {animals: [{id, name, species, age, photo_url, match_score, why_match: [reasons]}], total_count: N}
- [ ] Why_match explanation: human-readable list of reasons, e.g. ["Matches your experience level", "Good with other pets", "Can be alone 8+ hours"]
- [ ] Only return available animals: status='available', not adopted, not in quarantine
- [ ] Pagination: support limit and offset parameters (default limit 10)
- [ ] Filtering options: optional filters by species, age range, size (applied after matching)
- [ ] Performance: query should run in <1 second with optimized indexes
- [ ] Caching: cache match results for 1 hour per adopter profile (hash of answers)
- [ ] Edge cases: if no requirements defined for animal, return score=50 (neutral)
- [ ] Tie-breaking: if multiple animals have same score, sort by animal_id (deterministic)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test scoring algorithm, edge cases
- [ ] Integration test: match adopter with specific answers against sample animals
- [ ] Integration test: score calculation verified for various answer combinations
- [ ] Integration test: caching works correctly
- [ ] Integration test: filtering by species/age/size works
- [ ] Performance test: <1 second response time with 1000+ animals
- [ ] Manual testing: verify top matches are sensible
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoint /adoption/match, complex query logic
- Scoring: iterate animals, iterate requirements, compare answer to requirement value
- Requirement matching: for each requirement_type, implement matching logic
- Bonus points: add points for preference match, species match, experience match
- Caching: Redis key pattern "match_{answers_hash}", TTL 1 hour
- Indexes: create indexes on animal status, species, age for fast filtering
- Performance: use select() to fetch only needed columns, limit 10 per page
- Tie-breaking: sort by animal.id ASC as secondary sort
- Why_match: generate list of strings explaining each met requirement

## Story Points: 5
