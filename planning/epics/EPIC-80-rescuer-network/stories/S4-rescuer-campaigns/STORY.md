---
story: S4
epic: EPIC-80
ticket: RAP-536
title: "Rescuer campaign creation"
status: done
points: 5
priority: P1
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S4: Rescuer campaign creation

## Story
As a **rescuer**, I want **to create fundraising campaigns** so that **donors can support specific rescue efforts**.

## Description
Allow rescuers to create campaigns for specific animals or efforts (medical, transportation, shelter).

## Acceptance Criteria
- [ ] /portal/rescuer/campaigns page: list rescuer's campaigns with create button
- [ ] Create campaign: POST /api/rescuer/campaigns endpoint, form: title, description, target_amount (EUR), animals involved, photos, goal message
- [ ] Campaign published: immediately published (auto-approve for verified rescuers), requires admin approval for unverified
- [ ] Campaign page: /rescuers/{slug}/campaigns/{campaign_id} public page showing campaign details, progress bar, donor list, donate button
- [ ] Campaign status: active, completed, archived
- [ ] Donations tracked: donations with target_type='rescuer' and target_id=rescuer_id visible in campaign
- [ ] End campaign: rescuer can mark campaign as completed, triggers impact notification to donors

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: create campaign
- [ ] Integration test: campaign appears in rescuer profile
- [ ] Deployed to staging and verified

## Technical Notes
- Campaign model: title, description, target_amount, rescuer_id, status, created_at
- Auto-approval for verified rescuers, manual for unverified
- Donations aggregated for progress calculation

## Story Points: 5
