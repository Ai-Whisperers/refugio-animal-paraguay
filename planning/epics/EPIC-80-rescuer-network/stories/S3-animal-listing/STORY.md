---
story: S3
epic: EPIC-80
ticket: RAP-535
title: "Rescuer animal listing management"
status: ready
points: 8
priority: P0
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S3: Rescuer animal listing management

## Story
As a **rescuer**, I want **to list animals I'm rescuing** so that **donors and adopters can support them**.

## Description
Create interface for rescuers to add/manage animals needing homes, showing urgency and medical needs.

## Acceptance Criteria
- [ ] /portal/rescuer/animals page: list rescuer's animals with add button
- [ ] Add animal: POST /api/rescuer/animals endpoint, form: name, species (dog|cat|other), age, photos, description, medical_needs (textarea), urgency (low|medium|high|critical), status (available|adopted|in_treatment|deceased)
- [ ] Form validation: name required, species required, description 10-500 chars, at least 1 photo
- [ ] Public listing: /rescuers/{slug}/animals shows all status='available' animals with: photo, name, species, urgency badge, medical notes preview
- [ ] Status management: rescuer can change status (available -> adopted -> grateful, available -> in_treatment -> recovered -> available, etc.)
- [ ] Urgent animals: critical/high urgency highlighted with badge on listing
- [ ] Medical needs displayed: shows special needs (requires medication, surgery pending, etc.)
- [ ] Adoption story (optional): after adoption, rescuer can add "happy ending" story and photo
- [ ] Edit animal: rescuer can edit all details
- [ ] Delete animal: soft-delete (archive)
- [ ] Photos: can add up to 5 photos per animal

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test CRUD, status transitions
- [ ] Integration test: create animal and see in listing
- [ ] Integration test: edit animal
- [ ] Integration test: change status
- [ ] Component test: form renders and validates
- [ ] Manual testing: end-to-end workflow
- [ ] Deployed to staging and verified

## Technical Notes
- Animal model: extend existing Animal or create RescuerAnimal
- Status enum: available, adopted, in_treatment, deceased, archived
- Urgency affects listing order and highlighting
- Photos: store up to 5 per animal in cloud storage

## Story Points: 8
