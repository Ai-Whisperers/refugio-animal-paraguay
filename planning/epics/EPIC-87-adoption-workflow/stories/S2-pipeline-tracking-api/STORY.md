---
story: S2
epic: EPIC-87
ticket: RAP-589
title: "Pipeline status tracking API"
status: ready
points: 5
priority: P0
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S2: Pipeline status tracking API

## Story
As a **staff member**, I want **to move adoption applications through stages** so that **I can track progress**.

## Description
Extend AdoptionRequest model with current stage tracking. Implement API endpoints to advance applications through pipeline and log transitions.

## Acceptance Criteria
- [ ] AdoptionRequest model extended: current_stage_id (FK to AdoptionStage), current_stage_started_at (datetime)
- [ ] POST /api/admin/adoptions/{id}/advance endpoint moves application to next stage (auth: admin/staff)
- [ ] Validation before advance: check if current stage is complete (required fields filled)
- [ ] Request body: {notes (optional text for transition)}
- [ ] On advance: validate, create AdoptionStageLog, update current_stage_id, send notification to applicant
- [ ] POST /api/admin/adoptions/{id}/reject endpoint rejects application at any stage (auth: admin)
- [ ] Rejection creates log entry, sends notification to applicant with rejection reason
- [ ] Request body: {reason (text)}
- [ ] GET /api/admin/adoptions/{id}/history endpoint returns all stage transitions with dates and notes
- [ ] AdoptionStageLog model: adoption_request_id FK, from_stage_id FK, to_stage_id FK, notes (text), transitioned_by FK, transitioned_at (datetime)
- [ ] Notifications sent on stage advance: "Your adoption application moved to [stage name]"
- [ ] Notifications sent on rejection: "Your application was not approved. Reason: [reason]"
- [ ] GET /api/adoptions/{id} includes current_stage and days_in_current_stage
- [ ] Timeout detection: adoptions stuck in stage for configured timeout_days are flagged
- [ ] Unit tests: stage validation, transition logging, notifications

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for stage transitions and logging
- [ ] Notification logic tested
- [ ] Deployed to staging and verified

## Technical Notes
- Use transaction for atomic updates
- Store complete history in AdoptionStageLog
- Add audit trail with who moved and when
- Send notifications via email/WhatsApp

## Story Points: 5
