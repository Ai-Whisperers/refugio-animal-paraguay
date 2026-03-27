---
story: S8
epic: EPIC-86
ticket: RAP-587
title: "Emergency analytics"
status: ready
points: 3
priority: P2
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S8: Emergency analytics

## Story
As an **admin**, I want **to analyze emergency case patterns** so that **I can improve rapid response and prevention**.

## Description
Provide analytics dashboard for emergency cases. Track funding success, response times, patterns to help identify prevention opportunities.

## Acceptance Criteria
- [ ] GET /admin/emergencies/analytics endpoint returns metrics
- [ ] Metrics: total_emergencies (all time), success_count (funded), failure_count (expired/closed unfunded), success_rate (%)
- [ ] Average time to fund (in hours): track how long emergencies stay active before funding
- [ ] Average donation size per emergency (cents)
- [ ] Donor engagement: count unique donors per emergency, average donors per case
- [ ] Time series: emergencies created per week for last 3 months (trending)
- [ ] Common reasons: track if emergencies linked to common issues (surgery costs, injury, etc)
- [ ] Prevention opportunities: emergencies by animal type (dogs, cats, other), by rescuer (identify high-needs rescuers)
- [ ] Donor retention: count repeat donors (donated to multiple emergencies)
- [ ] /admin/dashboard includes "Emergency Analytics" summary widget: success rate, average funding time
- [ ] Admin can view detailed reports for individual emergencies
- [ ] Data exportable as CSV for further analysis

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Analytics calculated correctly from test data
- [ ] Dashboard displays metrics accurately
- [ ] CSV export tested
- [ ] Deployed to staging and verified

## Technical Notes
- Pre-calculate and cache analytics (update hourly)
- Store aggregated stats for performance
- Consider data warehouse for complex analysis
- Add monitoring for emergency creation rate (anomaly detection)

## Story Points: 3
