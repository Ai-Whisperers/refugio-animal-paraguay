---
story: S03
epic: EPIC-12
title: Foster Check-in Monitoring
status: ready
created: 2026-03-26T00:00:00.000000
effort: 6
---

# S03: Foster Check-in Monitoring

## User Story

As a **foster family**, I want to **submit regular check-in updates about my foster animal's health, behavior, and wellbeing with photos** so that **the shelter can monitor the animal's care and I can share updates about the animal's progress**.

## Acceptance Criteria

**Given** I am a foster family with an active placement
**When** I access the check-in submission form
**Then** I can submit health status, behavior observations, photos, and general notes

**Given** I submit a check-in
**When** staff reviews the submission
**Then** staff can see all check-in data and flag any concerns that need attention

**Given** a check-in indicates a health concern
**When** staff marks it as flagged
**Then** a notification is sent to the veterinary staff and shelter management

**Given** I have an active placement
**When** I attempt to submit a check-in
**Then** the system requires check-ins at least every 7 days (if configured by staff)

**Given** check-ins have been submitted regularly
**When** staff reviews the foster family's history
**Then** staff can see a timeline of check-ins and monitor animal progress

## Tasks

- T01: Implement foster check-in form with photo upload capability
- T02: Build check-in record persistence and attachment storage
- T03: Create staff review interface for monitoring check-ins
- T04: Implement concern flagging and notification workflow
- T05: Add check-in timeline visualization on placement detail view

## Definition of Done

- [ ] Check-in form validates all required fields (health status, behavior notes)
- [ ] Photo upload works with size/format validation (JPEG/PNG, max 5MB)
- [ ] Staff interface shows all check-ins for a placement with filtering options
- [ ] Flagging a concern sends notifications to vet and management
- [ ] Check-in timeline displays on foster family and staff dashboards
- [ ] Unit tests cover form validation and concern detection logic (80%+ coverage)
- [ ] Integration tests cover full check-in submission and staff review workflow
- [ ] Photo uploads stored securely with proper access controls

## Technical Notes

- Check-in model: id, placement_id, submitted_date, submitted_by_foster_id, health_status (enum), behavior_notes (text), general_notes (text), photo_urls (array), has_concerns (bool), concern_description (text)
- Health status enum: excellent, good, fair, poor, concerning
- Require authentication as the foster family assigned to the placement
- Implement rate limiting on photo uploads (max 5 photos per check-in)
- Store photos in S3 or similar with signed URLs for access
- Optional: schedule automated reminders for overdue check-ins

## Dependencies

- Depends on: S02-foster-placement-matching (active placement required)
- Depends on: EPIC-4 (Health/medical data structures)
- Blocks: S05-foster-supply-cost-tracking (cost estimates may depend on health status)

## Story Points: 6
