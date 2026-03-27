---
story: S2
epic: EPIC-81
ticket: RAP-544
title: "Animal sponsorship page"
status: ready
points: 5
priority: P0
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S2: Animal sponsorship page

## Story
As a **donor**, I want **to sponsor an animal monthly** so that **I can directly support their care**.

## Description
Create animal sponsorship page with monthly donation options showing impact of sponsorship.

## Acceptance Criteria
- [ ] Animal detail page /animals/{id}: includes "Sponsor [Name]" button
- [ ] /animals/{id}/sponsor page: shows animal photo, name, story, medical needs
- [ ] Sponsorship amounts: preset options EUR 10/20/50/100 per month, custom amount option
- [ ] Recurring donation: setup monthly recurring (subscription) with Stripe
- [ ] Impact description: "Your EUR 30/month covers food, medical care, and shelter"
- [ ] Sponsorship starts: "Set up monthly donation to [animal]", confirmation shows sponsor status
- [ ] Sponsor dashboard: sponsors see /portal/sponsors showing their sponsored animals
- [ ] Sponsor updates: send monthly updates to sponsor with animal photos, health status, news
- [ ] Payment method: credit card via Stripe Subscriptions
- [ ] Cancellation: sponsor can cancel subscription anytime from sponsor dashboard

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: create monthly donation
- [ ] Integration test: subscription set up in Stripe
- [ ] Component test: sponsorship page renders
- [ ] Manual testing: full sponsorship flow
- [ ] Deployed to staging and verified

## Technical Notes
- Recurring donation: target_type='animal', target_id=animal_id, is_recurring=true
- Stripe Subscriptions: create subscription with monthly interval
- Sponsor dashboard: show recurring donations with next_charge_date
- Updates: trigger monthly email to all sponsors with animal updates

## Story Points: 5
