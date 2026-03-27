---
story: S8
epic: EPIC-87
ticket: RAP-595
title: "Adoption success scoring"
status: ready
points: 5
priority: P2
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S8: Adoption success scoring

## Story
As an **admin**, I want **to measure adoption success** so that **I can identify effective practices and improve outcomes**.

## Description
Calculate adoption success score based on follow-up completion, issue reporting, and return status. Provides insights into adoption quality.

## Acceptance Criteria
- [ ] adoption_success_score field added to AdoptionRequest (0-100 scale)
- [ ] Score calculation based on: all follow-ups completed (+20 points each, max 100), no issues reported (+10 points), photos submitted (+5 points), no return request (+30 points), trial period passed (+20 points)
- [ ] Score calculated after each follow-up submission and trial completion
- [ ] Score visible on admin adoption detail page
- [ ] Historical score tracking: store score snapshots over time
- [ ] GET /admin/adoptions/analytics/success-scores returns aggregate metrics
- [ ] Metrics: average success score (all adoptions), success score trend (last 12 months), score distribution (A+/A/B/C grades)
- [ ] Adoptions can be graded: A+ (90-100), A (80-89), B (70-79), C (below 70)
- [ ] Grade shown on dashboard: color-coded (green, blue, yellow, red)
- [ ] Segment analysis: success score by animal type, by adopter region, by season
- [ ] Staff can view "Success Stories" (high-scoring adoptions with photos)
- [ ] Dashboard widget: "Average Success Score This Month" with trend indicator
- [ ] Export: CSV export of all adoption scores for analysis

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Score calculation verified with test data
- [ ] Analytics dashboard tested
- [ ] CSV export tested
- [ ] Trend calculations verified
- [ ] Deployed to staging and verified

## Technical Notes
- Calculate score with configurable weights (allow customization)
- Recalculate score retroactively for past adoptions
- Store score history for trend analysis
- Use background job for score recalculation
- Monitor for edge cases (incomplete follow-ups)
- Consider ML model for success prediction (future)

## Story Points: 5
