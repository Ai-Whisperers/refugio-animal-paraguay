---
story: S6
epic: EPIC-86
ticket: RAP-585
title: "Auto-close when funded"
status: ready
points: 3
priority: P1
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S6: Auto-close when funded

## Story
As a **system**, I want **to automatically close emergencies when funded** so that **we stop raising funds once goal is reached**.

## Description
Automatically update emergency status to 'funded' when donations reach amount_needed. Notify rescuer and donors. Update campaign status. Show surplus allocation option.

## Acceptance Criteria
- [ ] Scheduled job (Celery beat or similar) checks emergencies every minute
- [ ] When amount_raised >= amount_needed: set status = 'funded', set funded_at = now
- [ ] On funded: set linked Campaign status = 'funded' as well
- [ ] On funded: send email to rescuer: "Emergency funded! Raised [Amount] for [Animal]"
- [ ] On funded: send email to all donors: "Thanks for helping [Animal]! Emergency is fully funded. Here's what we'll do with the funds: [breakdown]"
- [ ] Breakdown email shows: amount allocated to [animal], admin/overhead, future cases (if over-funded)
- [ ] If over-funded (amount_raised > amount_needed): show surplus allocation UI: "We raised [X] extra! Choose where it goes: [Options]"
- [ ] Surplus options: donate to general fund, next emergency, castration campaign, other animals (rescuer selects)
- [ ] Update homepage emergency banner: remove from display once funded
- [ ] Show "FULLY FUNDED!" badge on emergency detail page
- [ ] If surplus exists, rescuer gets 1 week to choose allocation
- [ ] Unit tests: verify status updates, email sending

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: simulate funding emergency, verify status updates
- [ ] Scheduled job tested (run manually, verify behavior)
- [ ] Email notifications tested
- [ ] Homepage badge removal tested
- [ ] Deployed to staging and verified

## Technical Notes
- Use APScheduler or Celery Beat for scheduling
- Run job every minute (not super frequent, but responsive)
- Use transaction to ensure atomic updates
- Log all status changes for audit
- Consider webhook notification instead of scheduled job (event-driven)

## Story Points: 3
