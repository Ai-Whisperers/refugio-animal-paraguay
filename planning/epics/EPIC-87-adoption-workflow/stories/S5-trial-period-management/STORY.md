---
story: S5
epic: EPIC-87
ticket: RAP-592
title: "Trial period management"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S5: Trial period management

## Story
As a **staff member**, I want **to track trial periods for new adoptions** so that **we can ensure successful transitions**.

## Description
Create trial period tracking with automated check-in reminders. Adopters submit check-in forms at intervals (3, 7, 14 days). Staff reviews responses and marks trial as passed/failed.

## Acceptance Criteria
- [ ] TrialPeriod model: id (UUID), adoption_request_id (FK), start_date (date), end_date (date, default 14 days), check_in_schedule (JSON: [{day: 3, status: pending}, {day: 7}, {day: 14}]), status (enum: active, passed, failed, extended), created_at
- [ ] POST /api/admin/adoptions/{id}/trial-period creates trial (default 14 days)
- [ ] GET /api/adoptions/{id}/trial-period returns trial details
- [ ] Automated check-in reminders: at day 3, 7, 14, send email/WhatsApp to adopter asking "How is [animal] doing?"
- [ ] Check-in form: /adoptions/{id}/trial-checkin page with questions: "How is the animal doing?", photo uploads (1-3), any issues (text), happiness rating (1-5 stars)
- [ ] POST /api/adoptions/{id}/trial-checkin submits check-in response
- [ ] Staff reviews responses: /admin/adoptions/{id}/trial shows all check-ins
- [ ] PATCH /api/admin/adoptions/{id}/trial marks trial as passed or failed
- [ ] On passed: trial_status = passed, adoption can be finalized
- [ ] On failed: mark adoption as returned (S7), animal back to available
- [ ] Alert if issues reported: staff notified immediately if adopter reports problems
- [ ] Extend trial: staff can extend trial by X days if needed
- [ ] Trial completion email to adopter: confirmation of passed trial, congratulations

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: create trial, submit check-ins, review
- [ ] E2E test: complete trial workflow
- [ ] Reminder notifications tested
- [ ] Alert on issues tested
- [ ] Responsive design verified
- [ ] Deployed to staging and verified

## Technical Notes
- Use Celery Beat for scheduled reminders
- Store check-in responses for record keeping
- Implement photo upload reuse
- Add escalation if adopter misses check-in (e.g., email after 2 days late)
- Consider SMS as backup notification method

## Story Points: 5
