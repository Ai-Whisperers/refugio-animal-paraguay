---
story: S1
epic: EPIC-81
ticket: RAP-543
title: "Donation target type system"
status: ready
points: 5
priority: P0
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S1: Donation target type system

## Story
As a **system**, I want **to support flexible donation targets** so that **donors can direct support where they choose**.

## Description
Add target type system to Donation model allowing donations to animal, rescuer, clinic, campaign, or need.

## Acceptance Criteria
- [ ] Donation model: add target_type (enum: general|animal|rescuer|clinic|campaign|need), add target_id (UUID, nullable), migration
- [ ] Validation: if target_type != 'general', target_id must be valid and target must exist and be active
- [ ] Backward compatibility: existing donations without target_type default to 'general'
- [ ] API validation: POST /donations endpoint validates target exists, rejects if target inactive/deleted
- [ ] GET /donations endpoint: supports filtering by target_type and target_id
- [ ] Dashboard: donations grouped and displayed by target type
- [ ] Foreign keys: prevent deletion of target if donation references it (or soft-delete with constraint)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test validation, backward compatibility
- [ ] Database migration created
- [ ] Integration test: donate to each target type
- [ ] Integration test: validation prevents invalid targets
- [ ] Deployed to staging and verified

## Technical Notes
- Target types: general, animal, rescuer, clinic, campaign, need
- Validation: check target exists in appropriate table before accepting donation
- Backward compat: NULL target_type defaults to 'general'
- Indexes: (target_type, target_id) for efficient filtering

## Story Points: 5
