---
story: S1
epic: EPIC-86
ticket: RAP-580
title: "Emergency case model and creation API"
status: ready
points: 5
priority: P0
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S1: Emergency case model and creation API

## Story
As a **rescuer**, I want **to report emergency cases** so that **the community can help quickly**.

## Description
Create EmergencyCase model for urgent animal rescue situations. API endpoint allows verified rescuers to create cases which auto-create linked fundraising campaigns.

## Acceptance Criteria
- [ ] EmergencyCase model created: id (UUID), title (string), description (text), animal_id (FK to Animal, nullable), rescuer_id (FK to User), photos (JSON array of media_ids), amount_needed_cents (int), amount_raised_cents (int, default 0), currency (enum: USD, PYG), deadline (datetime), status (enum: active, funded, closed, expired), urgency (enum: high, critical), created_at (datetime), updated_at (datetime)
- [ ] Database migration with indexes on rescuer_id, status, urgency, deadline
- [ ] POST /api/emergencies endpoint creates case (auth: rescuer or staff role)
- [ ] Request body validation: title (required, max 200 chars), description (required), animal_id (optional), photos (optional, array of media IDs), amount_needed_cents (required, > 0), deadline (required, min 24 hours from now, max 30 days)
- [ ] Auto-generate Campaign linked to EmergencyCase on creation (emergency campaigns have is_emergency=true flag)
- [ ] Campaign title auto-filled: "[EMERGENCY] [EmergencyCase title]"
- [ ] Campaign auto-published (is_published=true) for verified rescuers
- [ ] Campaign target_amount_cents = emergency.amount_needed_cents
- [ ] Campaign deadline matches emergency deadline
- [ ] Response returns created EmergencyCase with campaign_id
- [ ] Status transitions: active -> funded -> closed (manual), or active -> expired (automatic on deadline pass)
- [ ] Soft delete implemented for archived cases
- [ ] Error handling: 403 if user not rescuer/staff, 400 for validation errors
- [ ] Unit tests cover: creation, validation, campaign linking

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for emergency creation and campaign linking
- [ ] Validation tested (all error cases)
- [ ] Deployed to staging and verified

## Technical Notes
- Use transaction to ensure case and campaign created together
- Validate deadline is in future (at least 24 hours)
- Reuse Campaign creation logic
- Add audit trail: who created, when
- Log all emergency creations

## Story Points: 5
