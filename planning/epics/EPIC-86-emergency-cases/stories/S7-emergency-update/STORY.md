---
story: S7
epic: EPIC-86
ticket: RAP-586
title: "Post-emergency update"
status: ready
points: 3
priority: P2
track: Fullstack
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S7: Post-emergency update

## Story
As a **rescuer**, I want **to share updates on emergency outcomes** so that **donors see the impact of their contribution**.

## Description
Allow rescuer to post text and photo updates to emergency case. Updates shown on timeline. Donors notified of updates.

## Acceptance Criteria
- [ ] EmergencyUpdate model: id (UUID), emergency_id (FK), text (text, max 1000 chars), photos (JSON array of media_ids), posted_by (FK to User), created_at
- [ ] /emergencies/{id}/updates GET endpoint returns all updates for emergency (most recent first)
- [ ] /emergencies/{id}/updates POST endpoint allows rescuer to post update (auth: rescuer or staff)
- [ ] Update form on emergency detail page: textarea for text, photo upload (1-3 photos)
- [ ] Posted updates displayed on /emergencies/{id} detail page in timeline format
- [ ] Timeline shows: date, update text, photos in grid
- [ ] When update posted: send email to all donors "Update on [Animal]: [preview of text]"
- [ ] Email includes link to full update on emergency page
- [ ] Rescuer can mark emergency as "Resolved" with final outcome
- [ ] Final outcome options: recovered, adopted, in-care, deceased, other
- [ ] Email to donors on resolution: "Here's what happened with [Animal]" with full outcome and photos
- [ ] Mobile responsive: full-width updates, stacked photos

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: post update, verify displayed, email sent
- [ ] E2E test: post update with photos, verify on emergency page
- [ ] Email notifications tested
- [ ] Responsive design verified
- [ ] Deployed to staging and verified

## Technical Notes
- Reuse MediaUploadField for photo uploads
- Use RichText editor for longer updates (optional)
- Implement optimistic updates
- Notify donors only once per day (batch notifications)

## Story Points: 3
