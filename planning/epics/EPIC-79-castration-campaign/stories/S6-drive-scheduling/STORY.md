---
story: S6
epic: EPIC-79
ticket: RAP-530
title: "Castration drive scheduling"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S6: Castration drive scheduling

## Story
As a **rescuer**, I want **to sign up for castration drives** so that **I can bring animals to be castrated**.

## Description
Create castration drive scheduling system. Clinics can schedule specific dates/locations, rescuers can register animals to be castrated.

## Acceptance Criteria
- [ ] CastrationDrive model: campaign_id (FK), clinic_id (FK), date (datetime), location (string), max_animals (integer), registered_count (integer, default 0), description
- [ ] POST /admin/campaigns/castration/{campaign_id}/drives endpoint: creates castration drive, requires: date, clinic, location, max_animals
- [ ] GET /campaigns/castration/{campaign_id}/drives endpoint: list upcoming drives (publicly visible), shows: date, clinic name, location, spots available
- [ ] GET /portal/volunteer/drives endpoint: for rescuers, shows available drives in their area with: date, clinic, location, max_animals, registered_count, "Sign Up" button
- [ ] Sign up flow: rescuer clicks "Sign Up", enters animals to bring (select from their animals list), commits to bringing them
- [ ] POST /api/rescuer/drives/{drive_id}/register endpoint: rescuer registers animals for drive, accepts: drive_id, animal_ids (array)
- [ ] Validation: registered_count + new_animals <= max_animals, validates animals belong to rescuer
- [ ] Confirmation: "You've registered X animals for [drive date] at [clinic]"
- [ ] Reminders: 48 hours before drive, send email/WhatsApp reminder with: date/time, location, what to bring, clinic address
- [ ] Drive page: /campaigns/castration/{campaign_id}/drives/{drive_id} shows full details with "Sign Up" button
- [ ] Admin can update/cancel drives

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test drive registration, capacity limits
- [ ] Integration test: create castration drive
- [ ] Integration test: rescuer registers animals
- [ ] Integration test: capacity limits enforced
- [ ] Integration test: reminder emails sent
- [ ] Component test: drive list displays correctly
- [ ] Manual testing: sign up flow works end-to-end
- [ ] Deployed to staging and verified

## Technical Notes
- CastrationDrive table: campaign_id, clinic_id, date, location, max_animals, registered_count
- Registration: POST endpoint validates rescuer auth and animal ownership
- Reminders: cron job 48h before drive to send notifications
- Location: geocoded for distance filtering (optional)
- Capacity: atomic check and update to prevent overbooking

## Story Points: 5
