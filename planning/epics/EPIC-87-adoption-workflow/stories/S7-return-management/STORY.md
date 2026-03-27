---
story: S7
epic: EPIC-87
ticket: RAP-594
title: "Return/exchange management"
status: ready
points: 3
priority: P2
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S7: Return/exchange management

## Story
As a **staff member**, I want **to process animal returns** so that **we can handle failed adoptions**.

## Description
Handle adoption returns/exchanges when adopters can't keep animals. Track return reason, animal condition, and whether it's an emergency. Return animal to available status.

## Acceptance Criteria
- [ ] ReturnRequest model: id (UUID), adoption_request_id (FK), reason (text, required), animal_condition (enum: healthy, injured, sick, deceased), is_emergency (bool), requested_by (FK to User), requested_at (datetime)
- [ ] POST /api/adoptions/{id}/return endpoint creates return request (auth: adopter or staff)
- [ ] Request body: {reason (text), animal_condition, is_emergency (bool)}
- [ ] On return: update adoption_request.status = 'returned'
- [ ] Update Animal.status = 'available' (if not injured/deceased)
- [ ] Trigger alert to staff: "Animal returned: [Animal Name]. Reason: [reason]"
- [ ] Store return in adoption history for record keeping
- [ ] Return reason analysis: track common reasons for pattern detection
- [ ] If emergency: flag for immediate assessment
- [ ] If animal injured/sick: create follow-up vet appointment reminder
- [ ] Adopter notification: "Thank you for returning [animal]. We appreciate you trying to help!"
- [ ] Staff can note: animal returned to foster, needs medical care, rehoming, etc
- [ ] Analytics: track return rate per animal type, per adoption stage, per adopter

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: process return, verify animal status updated
- [ ] Return reason tracking tested
- [ ] Analytics calculated correctly
- [ ] Deployed to staging and verified

## Technical Notes
- Implement soft delete for return requests (audit trail)
- Analyze return patterns monthly for insights
- Track return rate by adopter (identify problem adopters)
- Consider retry/retraining before making adopter ineligible

## Story Points: 3
