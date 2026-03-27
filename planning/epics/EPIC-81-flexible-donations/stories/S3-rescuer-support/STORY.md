---
story: S3
epic: EPIC-81
ticket: RAP-545
title: "Rescuer support page"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S3: Rescuer support page

## Story
As a **donor**, I want **to support a rescuer directly** so that **they can continue their work**.

## Description
Create rescuer support page with one-time and recurring donation options.

## Acceptance Criteria
- [ ] Rescuer profile /rescuers/{slug}: includes "Support [Name]" button
- [ ] /rescuers/{slug}/support page: shows rescuer bio, impact stats, support options
- [ ] Support options: one-time donation with amount input, monthly subscription with preset amounts (EUR 10/20/50/100)
- [ ] Impact message: "Your support helps [rescuer] save lives"
- [ ] Donor list: showing supporters (respecting anonymity) on rescuer profile, "X people supporting"
- [ ] Total support: show total monthly support received by rescuer
- [ ] Supporters see: /portal/supporters page listing rescuers they support with next charge date, cancel option

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: donate to rescuer (one-time and recurring)
- [ ] Component test: support page renders
- [ ] Manual testing: full flow
- [ ] Deployed to staging and verified

## Technical Notes
- Donation: target_type='rescuer', target_id=rescuer_id
- Recurring: is_recurring=true, Stripe Subscription created
- Supporter list: aggregate donations per rescuer, show on profile

## Story Points: 5
