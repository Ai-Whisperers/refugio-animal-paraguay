---
story: S4
epic: EPIC-87
ticket: RAP-591
title: "Home visit scheduling"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S4: Home visit scheduling

## Story
As a **staff member**, I want **to schedule home visits for adoptions** so that **I can verify living conditions**.

## Description
Add home visit scheduling to adoption process. Staff schedules visit, adopter receives notification. Stores visit details: date, address, staff member, outcome.

## Acceptance Criteria
- [ ] HomeVisit model: id (UUID), adoption_request_id (FK), scheduled_at (datetime), address (text), staff_id (FK to User), status (enum: scheduled, completed, cancelled), notes (text), photos (JSON array of media_ids), created_at
- [ ] GET /api/admin/adoptions/{id}/home-visits endpoint returns scheduled visits
- [ ] POST /api/admin/adoptions/{id}/home-visits creates home visit (auth: admin/staff)
- [ ] Request body: {scheduled_at (datetime), address (text), staff_id (user_id)}
- [ ] On creation: send email to adopter with date+time+address, send WhatsApp reminder to adopter
- [ ] Auto-send 24-hour reminder: Celery task sends email/WhatsApp reminder 24h before scheduled visit
- [ ] PUT /api/admin/home-visits/{id} updates visit details
- [ ] PATCH /api/admin/home-visits/{id}/complete completes visit: {status, notes, photos}
- [ ] Calendar integration: home visits visible on calendar (staff member view, date view)
- [ ] Adopter receives confirmation email with staff member contact info
- [ ] Visit completion email to adopter: "Thank you for home visit!"
- [ ] Visit notes and photos stored for record keeping
- [ ] Adopter can view their scheduled home visits on portal

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: schedule visit, verify notifications
- [ ] E2E test: complete workflow from scheduling to completion
- [ ] Reminder notifications tested
- [ ] Calendar integration tested
- [ ] Responsive design verified
- [ ] Deployed to staging and verified

## Technical Notes
- Use calendar library (react-big-calendar) for calendar view
- Implement reminders with Celery Beat (24h before)
- Store address for reference, verify format
- Reuse photo upload component
- Add staff member availability calendar check (optional future)

## Story Points: 5
