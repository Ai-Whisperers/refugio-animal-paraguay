---
story: S7
epic: EPIC-81
ticket: RAP-549
title: "Impact notification system"
status: ready
points: 5
priority: P2
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S7: Impact notification system

## Story
As a **donor**, I want **to receive notifications about how my donation was used** so that **I see the impact of my support**.

## Description
Send donors notifications when donations are allocated and monthly impact digests for recurring donors.

## Acceptance Criteria
- [ ] When donation allocated: send email "Your EUR 50 helped castrate 2 animals at Clinica San Lorenzo", include: expense description, date, animals helped (if applicable)
- [ ] Allocation notification: sent to donor within 24h of allocation
- [ ] Monthly digest (recurring donors): "This month your recurring donation helped: [summary]", include metrics and photos
- [ ] Monthly digest email: sent on 1st of month to all recurring donors, aggregated across all targets
- [ ] Email template: personalized, HTML formatted, includes: donor name, total donated this month, impact summary, photos/stories
- [ ] WhatsApp option: if donor opted in for WhatsApp, send shorter version via WhatsApp
- [ ] Opt-in preference: donors can control notification frequency (immediate|weekly|monthly|off) in preferences
- [ ] Photo inclusion: include animal/program photos if available (with consent)
- [ ] Unsubscribe: every email includes unsubscribe link

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test email generation, templates
- [ ] Integration test: allocation triggers notification email
- [ ] Integration test: monthly digest email generated correctly
- [ ] Integration test: donor preferences respected
- [ ] Manual testing: email rendering and content
- [ ] Deployed to staging and verified

## Technical Notes
- Event trigger: when DonationAllocation created, send email to donation.donor_id
- Email templates: Jinja2 templates for allocation and monthly digest
- Monthly digest: cron job on 1st of each month, query donations and allocations for each recurring donor
- Preferences: notification_frequency in user_preferences table
- Unsubscribe: PUT /api/users/notifications/unsubscribe/{token}

## Story Points: 5
