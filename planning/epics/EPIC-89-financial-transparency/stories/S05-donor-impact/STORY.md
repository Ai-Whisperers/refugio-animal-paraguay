---
story: S5
epic: EPIC-89
ticket: RAP-608
title: "Donor impact summaries"
status: done
points: 6
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S05: Donor Impact Summary

## Story

As a donor, I want to see a personalized summary of how my donations have been used and what impact they've created so that I feel motivated to continue supporting the organization.

## Description

Implement personalized impact summary API endpoint for authenticated donors. Calculate allocation of their donations to expense categories and outcomes, and provide compelling impact statements like "Your donations helped rescue X animals" or "Fed N animals for N days."

## Acceptance Criteria

- [ ] Implement GET /api/portal/impact endpoint (requires authentication, donor role)
- [ ] Response includes:
  - [ ] Total donated (all time in PYG and USD)
  - [ ] Total donated (last 12 months)
  - [ ] Allocation breakdown: percentage by category
    - [ ] X% Medical (Medico)
    - [ ] Y% Food (Comida)
    - [ ] Z% Shelter (Refugio)
    - [ ] etc.
- [ ] Calculate impact metrics based on expenses:
  - [ ] "Your donations helped rescue N animals"
  - [ ] "Your donations funded N emergency rescues"
  - [ ] "Your donations helped castrate N animals"
  - [ ] "Your donations provided medical care for N animals"
  - [ ] "Your donations provided food for N animals for N days"
- [ ] Impact statistics calculated from:
  - [ ] Emergency cases funded (count where category=rescue)
  - [ ] Castrations funded (count medical procedures)
  - [ ] Animals fed (estimate days from food expenses)
  - [ ] Animals treated (count medical records)
- [ ] Support multiple currencies in response
- [ ] Include "Comparison to goals" if goals defined:
  - [ ] "You're #N donor by amount this year"
  - [ ] "You've contributed X% to castration goal"
- [ ] Personalize impact statement: use donor's name
- [ ] Include "Top campaigns" supported (sort by donation amount)
- [ ] Response format:
  ```json
  {
    "total_donated": 500000,
    "currency": "PYG",
    "allocation": {"medical": 0.4, "food": 0.3, "shelter": 0.2, "rescue": 0.1},
    "impact": {
      "animals_rescued": 15,
      "emergency_cases_funded": 3,
      "castrations_funded": 12,
      "animals_fed_estimate_days": 180
    },
    "top_campaigns": [...],
    "comparison": "You're #5 donor this year"
  }
  ```
- [ ] Cache result per donor (1 day TTL)
- [ ] Query performance optimized for real-time calculation

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] API endpoint implemented and tested
- [ ] Impact calculations verified against actual expenses
- [ ] Caching configured (1 day TTL)
- [ ] Unit tests for impact calculations
- [ ] Integration test for API endpoint
- [ ] Data accuracy verified with sample donors
- [ ] Performance tested (query <1s for large donor)
- [ ] Error handling for donors with no donations
- [ ] Documentation of impact calculation methodology
- [ ] Deployed to staging and verified

## Technical Notes

- Pre-aggregate impact statistics nightly
- Cache results in Redis per donor
- Use database views for complex calculations
- Estimate days of food based on average daily cost
- Handle edge cases: zero donations, negative expenses (refunds)
- Consider rounding impact numbers (show ranges if uncertain)
- Document methodology for impact statements (how counted, assumptions)

## Story Points: 5
