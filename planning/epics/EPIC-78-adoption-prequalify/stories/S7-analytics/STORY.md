---
story: S7
epic: EPIC-78
ticket: RAP-523
title: "Pre-qualification analytics"
status: ready
points: 3
priority: P2
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S7: Pre-qualification analytics

## Story
As an **adoption administrator**, I want **to see pre-qualification analytics** so that **I can understand adoption funnel and improve process**.

## Description
Track pre-qualification metrics to understand pass rates, bottlenecks, and conversion efficiency.

## Acceptance Criteria
- [ ] GET /admin/adoption/pre-qualify/analytics endpoint: returns analytics dashboard data, requires admin auth
- [ ] Metrics returned: total_attempts (all-time), pass_rate (% qualified), fail_rate (%), most_common_disqualifying_factors (list with counts), conversion_rate (pre-qual -> full application), average_score
- [ ] Most_common_disqualifying_factors: count of each failed requirement type, e.g. {requirement_type: 'yard_required', count: 1234}
- [ ] Conversion rate: (number of users who applied after pre-qual / number of users who passed pre-qual) * 100
- [ ] Conversion rate (detailed): show by animal (which animals have highest conversion)
- [ ] Average score distribution: breakdown of scores (0-20%, 20-40%, 40-60%, 60-80%, 80-100%)
- [ ] Time series: daily/weekly/monthly data (attempts, pass rate) for trend analysis
- [ ] Filter by date range: support start_date and end_date parameters
- [ ] Filter by animal: show analytics for specific animal if animal_id provided
- [ ] Response format: {total_attempts, pass_rate, fail_rate, most_common_disqualifying_factors, conversion_rate, average_score, score_distribution, time_series}
- [ ] Logging: all pre-qual attempts logged for analytics (including failed attempts with reason)
- [ ] Note: these are stats-only, no PII exposed

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test metric calculations
- [ ] Integration test: verify pass_rate calculation
- [ ] Integration test: verify conversion_rate calculation
- [ ] Integration test: verify disqualifying factors sorted by count
- [ ] Integration test: date range filtering works
- [ ] Integration test: animal filtering works
- [ ] Manual testing: verify numbers match database queries
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoint /admin/adoption/pre-qualify/analytics
- Logging: store pre-qual attempts in analytics table or separate log storage
- Pass rate calculation: (qualified_attempts / total_attempts) * 100
- Fail rate calculation: 100 - pass_rate
- Disqualifying factors: group by failed_requirement type, count, sort by count DESC
- Conversion rate: complex query joining pre-qual attempts with applications
- Score distribution: bucket scores into ranges, count per bucket
- Time series: group by DATE(created_at), calculate daily metrics
- Indexes: create on created_at, animal_id for efficient aggregations
- Caching: cache analytics results (5-minute TTL) since calculations are expensive

## Story Points: 3
