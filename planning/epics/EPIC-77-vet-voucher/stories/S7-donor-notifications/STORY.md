---
story: S7
epic: EPIC-77
ticket: RAP-513
title: "Donor transparency notifications"
status: ready
points: 3
priority: P1
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S7: Donor transparency notifications

## Story
As a **donor**, I want **to receive notifications when my vouchers are claimed and redeemed** so that **I know my donation is helping animals**.

## Description
Send timely notifications to donors tracking their voucher usage from purchase through redemption. Include monthly summaries of activity.

## Acceptance Criteria
- [ ] Event: When rescuer claims voucher, send email to donor with: subject "Your voucher has been claimed!", message "A rescuer has claimed your [service type] voucher at [clinic name] for [animal name]", include animal photo if available
- [ ] Event: When clinic redeems voucher, send email to donor with: subject "Your voucher helped an animal!", message "Your [service type] voucher was redeemed at [clinic name] for [animal name]", include proof photo from clinic (if permissions allow), brief description of animal
- [ ] Email format: HTML with logo, clear formatting, mobile-responsive
- [ ] WhatsApp option: if donor opted in for WhatsApp, send WhatsApp message instead of/in addition to email with same content (shorter format)
- [ ] Notification preferences: donors can control via /portal/settings: "Email notifications for voucher updates" (checkbox), "WhatsApp notifications for voucher updates" (checkbox), default both checked
- [ ] Monthly summary email: sent on 1st of month with: total vouchers purchased last month, total redeemed, total claimed, animals helped (with photos), clinics partnered with, impact message ("Your EUR 150 helped 3 animals!")
- [ ] Email triggers: create notification records in database when events occur, cron job sends emails (not synchronously), retry logic for failed sends
- [ ] Database: notification_events table with columns: id (UUID PK), user_id (FK), event_type (enum: voucher_claimed|voucher_redeemed|monthly_summary), voucher_id (FK, nullable for monthly), created_at, sent_at, retry_count
- [ ] Notification template engine: use Jinja2 templates for email bodies, support variables like {donor_name}, {animal_name}, {clinic_name}, {service_type}
- [ ] Rate limiting: max one email per user per hour (batch notifications if multiple events occur)
- [ ] Unsubscribe option: every email includes unsubscribe link that updates user preferences

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test event triggers, template rendering, notification creation
- [ ] Integration test: claim triggers notification to donor
- [ ] Integration test: redeem triggers notification to donor
- [ ] Integration test: monthly summary email generated correctly
- [ ] Integration test: notification preferences respected
- [ ] Integration test: retry logic works for failed sends
- [ ] Email template tests: verify rendering with sample data
- [ ] Manual testing: send test emails and verify formatting
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints, notification event creation on claim/redeem, cron job for monthly summary (celery beat or APScheduler)
- Email templates: Jinja2 templates at templates/emails/, one per event type
- Template rendering: render with context dict containing all variables, convert to HTML
- WhatsApp: use Twilio API, send if donor opted in and WhatsApp number available
- Notification queue: use email service provider queue (Mailgun, SendGrid), retry automatic
- Unsubscribe: include unsubscribe link that calls PUT /api/users/notifications/unsubscribe with token
- Monthly summary: query VetVouchers from last month, aggregate by donor, generate summary
- Rate limiting: check last sent_at timestamp, queue if < 1 hour since last email
- Opt-in/out: respect notification_preferences from user record

## Story Points: 3
