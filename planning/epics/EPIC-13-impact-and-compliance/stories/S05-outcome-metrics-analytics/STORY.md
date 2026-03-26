---
story: S05
epic: EPIC-13
title: Outcome Metrics & Analytics
status: ready
created: 2026-03-26T00:00:00.000000
effort: 7
---

# S05: Outcome Metrics & Analytics

## User Story

As a **shelter director or researcher**, I want to **track post-adoption outcomes and measure adoption success metrics** so that **I can quantify program effectiveness, identify trends, and improve adoption practices**.

## Acceptance Criteria

**Given** an animal is adopted
**When** 30 days, 90 days, 6 months, and 1 year pass
**Then** staff can send follow-up surveys to adopters asking about animal's health, behavior, and satisfaction

**Given** follow-up data is collected
**When** I view the analytics dashboard
**Then** I see return rate (%, by species), adoption success rate (%), average time-to-adoption, and cost-per-adoption trends

**Given** I am analyzing adoption outcomes
**When** I filter by species or time period
**Then** outcomes are segmented and I can identify which types of placements have highest success rates

**Given** adoption return rate is high for a specific species
**When** I investigate the data
**Then** I can see which adopters returned animals and why (incompatibility, behavior, health)

**Given** I need to report on shelter effectiveness
**When** I generate an outcome report
**Then** it includes adoption success rate, average time-to-adoption, cost-per-adoption, return rate, and trends

## Tasks

- T01: Design and implement post-adoption follow-up survey schema and survey delivery system
- T02: Build analytics dashboard with outcome metrics (return rate, success rate, time-to-adoption, cost-per-adoption)
- T03: Implement automated follow-up survey scheduling (30d, 90d, 6m, 1y post-adoption)
- T04: Create outcome analytics export functionality (CSV for research/analysis)
- T05: Add outcome metrics to impact reporting and strategic dashboards

## Definition of Done

- [ ] Post-adoption follow-up surveys sent automatically on schedule
- [ ] Survey responses captured and stored with adoption record linkage
- [ ] Analytics dashboard displays all outcome metrics correctly calculated
- [ ] Metrics filterable by species, time period, and adoption source
- [ ] Return rate calculated as: adoptions_returned / total_adoptions
- [ ] Success rate calculated as: adoptions_not_returned / total_adoptions
- [ ] Unit tests cover metric calculations and aggregations (85%+ coverage)
- [ ] Integration tests verify full survey workflow and outcome tracking
- [ ] Survey response optional (not mandatory for adoption closure)

## Technical Notes

- Post-adoption follow-up model: id, adoption_id, scheduled_date, sent_date, response_date, response_data (JSON), return_requested (bool), return_reason (text)
- Outcome metrics: return_rate (%), success_rate (%), avg_time_to_adoption_days, cost_per_adoption, return_count, success_count
- Survey questions: animal_health (scale 1-5), behavior_satisfaction (scale 1-5), family_satisfaction (scale 1-5), would_recommend (yes/no), return_reason (if applicable)
- Scheduling: use Celery or background jobs to send surveys on fixed intervals
- Analytics aggregation: by species, by time period, by adoption source (direct, website, partner org)
- Trend analysis: compare metrics across quarters/years to identify improvement areas
- Optional: machine learning to predict adoption success risk factors

## Dependencies

- Depends on: EPIC-2 (Adoption process and tracking)
- Depends on: EPIC-6 (Communications/surveys)
- Depends on: S04-fund-allocation-tracking (cost-per-adoption requires fund allocation data)
- Blocks: None (terminal story)

## Story Points: 7
