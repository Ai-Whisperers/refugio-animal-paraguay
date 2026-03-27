---
story: S5
epic: EPIC-81
ticket: RAP-547
title: "Need-specific donation"
status: ready
points: 3
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S5: Need-specific donation

## Story
As a **donor**, I want **to donate to a specific community need** so that **I can help urgent requests**.

## Description
Enable donations to specific needs posted on community needs board.

## Acceptance Criteria
- [ ] Community needs page: /community/needs shows "Help with this" button on each need
- [ ] Donation flow: click button, select amount, pay via Stripe/SEPA
- [ ] Donation target: target_type='need', target_id=need_id
- [ ] Auto-closure: when need is funded to estimated_cost, auto-mark need as fulfilled
- [ ] Notifications: notify need creator when donated to
- [ ] Need page: shows total raised vs goal (if goal set), donors count (with anonymity)
- [ ] Refund policy: if need cancelled, refund donors (or rollover to platform account)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: donate to need
- [ ] Integration test: auto-closure when funded
- [ ] Deployed to staging and verified

## Technical Notes
- Donation: target_type='need', target_id=need_id
- Auto-closure: sum donations to need, if >= estimated_cost, set status='fulfilled'
- Refund: if need cancelled, process refunds atomically

## Story Points: 3
