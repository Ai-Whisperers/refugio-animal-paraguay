---
story: S6
epic: EPIC-87
ticket: RAP-593
title: "Post-adoption follow-up automation"
status: ready
points: 5
priority: P1
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S6: Post-adoption follow-up automation

## Story
As a **system**, I want **to automatically schedule follow-ups** so that **we maintain contact with adopters post-adoption**.

## Description
On adoption approval, automatically schedule follow-ups at 1 week, 1 month, 3 months, 6 months, 1 year. Adopters receive questionnaires and can report issues.

## Acceptance Criteria
- [ ] On adoption approval: create FollowUpSchedule with auto-generated scheduled dates
- [ ] Follow-up schedule: 1 week, 1 month, 3 months, 6 months, 1 year from approval_date
- [ ] FollowUpSchedule model: id (UUID), adoption_request_id (FK), scheduled_date (datetime), status (pending, completed, skipped), response (JSON), responded_date (datetime)
- [ ] At each scheduled date: send email/WhatsApp to adopter with follow-up questionnaire link
- [ ] Questionnaire: "How is [animal] doing?", "Any health issues?", "Behavior challenges?", "Overall happiness (1-5)", "Photos" (upload optional)
- [ ] POST /api/adoptions/{id}/follow-up/{schedule_id}/respond submits response
- [ ] Staff can view all follow-up responses: /admin/adoptions/{id}/follow-ups
- [ ] Alert system: if any issue reported, notify staff immediately
- [ ] Follow-up completion tracked: dashboard shows % of follow-ups completed per adoption
- [ ] Email reminders: send reminder if follow-up not completed 3 days after scheduled date
- [ ] Skip option: adopter can mark "Prefer not to respond" (respects privacy)
- [ ] Celery Beat job runs daily to send due follow-up emails and alerts

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: adoption approval triggers follow-up creation
- [ ] Celery job tested (send follow-ups on schedule)
- [ ] Alert system tested (issues trigger notifications)
- [ ] Dashboard metrics calculated correctly
- [ ] Deployed to staging and verified

## Technical Notes
- Use Celery Beat for scheduled emails
- Store all responses for post-adoption analysis
- Implement response tracking with timestamps
- Alert staff on first response to critical questions
- Consider SMS reminders for low engagement

## Story Points: 5
