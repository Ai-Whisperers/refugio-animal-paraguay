---
story: S5
epic: EPIC-79
ticket: RAP-529
title: "Donor leaderboard"
status: ready
points: 3
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S5: Donor leaderboard

## Story
As a **donor**, I want **to see top donors for campaign** so that **I can see impact and be inspired to donate more**.

## Description
Display leaderboard of top donors by amount contributed to campaign, with opt-in anonymity option.

## Acceptance Criteria
- [ ] Leaderboard section on campaign page: shows top 10 donors by total amount donated to this campaign
- [ ] Display: rank, donor name (or "Anonymous"), total donated amount (EUR), date joined campaign (first donation date)
- [ ] Anonymity: donor can opt-in to remain anonymous in leaderboard, shown as "Anonymous"
- [ ] Anonymous by default for amounts < EUR 10
- [ ] Show donor count: "X donors supporting this campaign"
- [ ] Opt-in toggle: /portal/settings allows donor to control leaderboard visibility
- [ ] API endpoint: GET /api/campaigns/castration/{id}/leaderboard returns top 10 donors
- [ ] Response format: {rank, donor_name_or_anonymous, amount_cents, currency, donation_date}

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test leaderboard ranking, anonymity
- [ ] Component test: leaderboard renders correctly
- [ ] Integration test: top donors listed correctly by amount
- [ ] Integration test: anonymity respected
- [ ] Manual testing: verify leaderboard accuracy
- [ ] Deployed to staging and verified

## Technical Notes
- Leaderboard query: GROUP BY user aggregating donations to campaign, sort by total DESC, limit 10
- Anonymity: check donor.leaderboard_visibility flag
- Total donation: sum all donations for campaign from donor
- Response: serialize with anonymity rules applied

## Story Points: 3
