---
story: S5
epic: EPIC-80
ticket: RAP-537
title: "Needs board"
status: done
points: 5
priority: P1
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S5: Needs board

## Story
As a **rescuer**, I want **to post urgent needs** so that **community can quickly help**.

## Description
Create community needs board where rescuers and animal organizations post urgent requests (food, transport, supplies, medical).

## Acceptance Criteria
- [ ] /community/needs public page: shows all open needs, filterable by type and location
- [ ] Post need: /portal/rescuer/needs page with form: title, description, need_type (food|transport|foster|medical|supplies|other), urgency (low|medium|high|critical), location, contact_method (email|whatsapp|phone), target_date (by when needed), estimated_cost (optional)
- [ ] Needs listing: shows: need title, urgency badge, type icon, location, date posted, "Help with this" button
- [ ] Need detail page: /community/needs/{id} shows full details, contact information, "Respond to need" button
- [ ] Status management: rescuer can mark need as open/fulfilled/cancelled
- [ ] Community responses: show responses/offers to help (optional)
- [ ] Urgent highlighting: critical/high urgency highlighted, pinned at top
- [ ] Time decay: older needs deprioritized in listing
- [ ] Response button: "Help with this" can donate money to need, or contact rescuer directly

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: post need and see in listing
- [ ] Integration test: mark need fulfilled
- [ ] Component test: responsive UI
- [ ] Deployed to staging and verified

## Technical Notes
- CommunityNeed model: rescuer_id, title, description, need_type, urgency, location, contact, target_date, status
- Urgent needs shown first, then by created_at DESC
- Filtering by type and location
- Status options: open, fulfilled, cancelled

## Story Points: 5
