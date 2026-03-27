---
story: S1
epic: EPIC-91
ticket: RAP-618
title: "Transport request model and API"
status: ready
points: 4
priority: P0
track: Backend
sprint: 15
version: V15
created: 2026-03-27T20:00:00
---
# S01: Transport Request Model and API

## Story
As a rescuer, I want to request animal transport for urgent cases so that injured animals reach veterinary clinics quickly.

## Acceptance Criteria
- [ ] TransportRequest model with: requester_id, animal_id, pickup_location, destination, urgency, preferred_date/time, status, notes
- [ ] Status enum: open, claimed, in_transit, delivered, cancelled
- [ ] Urgency enum: normal, urgent, emergency
- [ ] POST /api/transport - create request (auth required)
- [ ] GET /api/transport/{id} - get request details
- [ ] PUT /api/transport/{id} - update request
- [ ] DELETE /api/transport/{id} - cancel request
- [ ] Validate location fields (text description or coords)
- [ ] Validate urgency and status enums
- [ ] Return proper HTTP status codes

## Definition of Done
- [ ] Model and API endpoints tested
- [ ] Validation working
- [ ] Database migration created
- [ ] Deployed to staging

## Story Points: 5
