---
story: S1
epic: EPIC-85
ticket: RAP-573
title: "Public statistics API"
status: ready
points: 3
priority: P0
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S1: Public statistics API

## Story
As a **public user**, I want **to see organization statistics** so that **I understand the impact**.

## Description
Create a public API endpoint that returns aggregated statistics about rescued animals, adoptions, castrations, donations. No authentication required. Cached to prevent performance issues.

## Acceptance Criteria
- [ ] GET /api/stats/public endpoint created (no auth required)
- [ ] Returns JSON with: total_animals_rescued (count from animals table), total_adopted (count of completed adoptions), total_castrated (count of surgeries where type='castration'), total_donors (count of unique donors), total_donations_amount_cents (sum of all donations), total_volunteers (count of users with volunteer role)
- [ ] Response includes currency_code for donations (USD, PYG, or other)
- [ ] Response cached for 5 minutes (Redis or in-memory cache)
- [ ] Cache invalidation: automatically on animal creation, adoption completion, surgery creation, donation completion
- [ ] Error handling: return 500 with error message if calculation fails
- [ ] Response time target: <100ms (achieved via caching)
- [ ] Response format: JSON with timestamp of last update
- [ ] Unit tests: verify correct calculation of each metric

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: verify numbers match database totals
- [ ] Performance verified: <100ms response time
- [ ] Cache invalidation tested
- [ ] Deployed to staging and verified

## Technical Notes
- Use Redis for caching if available, fall back to in-memory
- Implement cache warming on startup (pre-calculate)
- Monitor cache hit rate
- Consider storing snapshots for history (timestamp, metrics)

## Story Points: 3
