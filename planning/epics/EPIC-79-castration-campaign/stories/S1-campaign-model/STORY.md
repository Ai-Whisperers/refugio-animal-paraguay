---
story: S1
epic: EPIC-79
ticket: RAP-525
title: "Castration campaign model and creation API"
status: ready
points: 5
priority: P0
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S1: Castration campaign model and creation API

## Story
As a **campaign manager**, I want **to create castration campaigns** so that **I can organize coordinated spay/neuter efforts**.

## Description
Create CastrationCampaign model extending Campaign with castration-specific fields. Allow admin to create campaigns with target numbers and partner clinics.

## Acceptance Criteria
- [ ] CastrationCampaign model/table extending Campaign with: target_count (integer, animals to castrate), completed_count (integer, default 0), partner_clinics (M2M relationship to VetClinic), target_area (string, location description), start_date, end_date, campaign_type='castration'
- [ ] POST /admin/campaigns/castration endpoint: creates new castration campaign, accepts: title, description, target_count, partner_clinic_ids (array), target_area, start_date, end_date, goal_message (motivational text)
- [ ] Validation: target_count > 0, end_date > start_date, at least one partner clinic, title 5-200 chars, description 10-1000 chars
- [ ] Response: returns created campaign with all fields
- [ ] GET /admin/campaigns/castration endpoint: list all castration campaigns with: title, target_count, completed_count, progress_percent, status (active|completed|planned)
- [ ] GET /admin/campaigns/castration/{id} endpoint: detailed campaign view with all fields and partner clinics list
- [ ] PUT /admin/campaigns/castration/{id} endpoint: update campaign details, validates fields, prevents changes to completed_count (read-only)
- [ ] Campaign status: 'planned' if start_date in future, 'active' if between start/end dates, 'completed' if end_date in past
- [ ] Completed count auto-increment: when voucher redeemed for castration_dog or castration_cat service at partner clinic, increment completed_count
- [ ] Partner clinics M2M table: campaign_id, clinic_id, created_at
- [ ] Database migration: CastrationCampaign and castration_campaign_clinics junction table

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test campaign creation, status calculation, completed_count increment
- [ ] Integration test: create castration campaign
- [ ] Integration test: update campaign details
- [ ] Integration test: partner clinics associated correctly
- [ ] Integration test: completed_count increments on castration voucher redemption
- [ ] Database migration created and tested
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints in admin/campaigns module
- CastrationCampaign: inherit from Campaign base model (if exists) or create new
- Partner clinics: use SQLAlchemy many-to-many relationship
- Status calculation: compare dates to determine current status
- Completed count: trigger increment from vet_voucher redemption event (S3)
- M2M junction: castration_campaign_clinics table
- Validation: target_count >= 1, at least one clinic, dates valid

## Story Points: 5
