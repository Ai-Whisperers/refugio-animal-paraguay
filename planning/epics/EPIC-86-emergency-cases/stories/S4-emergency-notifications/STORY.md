---
story: S4
epic: EPIC-86
ticket: RAP-583
title: "Push notifications to donors"
status: ready
points: 3
priority: P1
track: Backend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S4: Push notifications to donors

## Story
As an **admin**, I want **to notify donors about emergencies** so that **we can mobilize support quickly**.

## Description
When emergency case created, send email and WhatsApp messages to opted-in donors. Include emergency details and direct donate link.

## Acceptance Criteria
- [ ] On EmergencyCase creation: check Donor.notification_preferences.emergency_alerts = true
- [ ] For each interested donor: send email notification
- [ ] Email template: Subject "EMERGENCY: [Animal], needs [Amount]", body includes photo, description, deadline, "Donate Now" button link to /emergencies/{id}/donate
- [ ] Send WhatsApp to donors with verified phone numbers (check User.phone_verified)
- [ ] WhatsApp message: "EMERGENCIA: [animal_name] necesita [amount]! [URL]" (respects character limit)
- [ ] Notification rate limit: max 1 emergency notification per donor per day (prevent alert fatigue)
- [ ] Respect donor's notification preferences: only send if they opted in
- [ ] Track notification sending: log which donors received notifications
- [ ] Fallback: if email fails, don't block case creation, log error
- [ ] Fallback: if WhatsApp fails, don't block, log error (retry later)
- [ ] Admin dashboard shows "Notifications sent: X emails, Y WhatsApp" after case creation
- [ ] Unit tests: verify notifications queued correctly

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: create emergency, verify notifications queued
- [ ] Manual test: verify email and WhatsApp received
- [ ] Rate limiting tested
- [ ] Preference respect tested (opt-out donors don't receive)
- [ ] Deployed to staging and verified

## Technical Notes
- Use email/WhatsApp service from infrastructure (SendGrid, Twilio)
- Implement async notification sending (Celery task queue)
- Track delivery status (bounced, sent, failed)
- Use templating system for email body
- Implement retry logic with exponential backoff

## Story Points: 3
