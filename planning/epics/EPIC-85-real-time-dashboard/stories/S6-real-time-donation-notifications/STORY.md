---
story: S6
epic: EPIC-85
ticket: RAP-578
title: "Real-time donation notifications"
status: ready
points: 5
priority: P1
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S6: Real-time donation notifications

## Story
As an **admin**, I want **to be notified when donations arrive** so that **I can acknowledge donors quickly**.

## Description
When a donation completes, trigger real-time notifications on admin dashboard, optional audio alert, and toast message with donation details. Uses event bus for decoupling.

## Acceptance Criteria
- [ ] On donation completion: emit DonationCreatedEvent to event bus (domain event pattern)
- [ ] Event listener publishes to SSE stream for admin activity feed (S5)
- [ ] Toast notification shown on admin dashboard: "Donation received! [Donor Name] donated [Amount] [Currency]"
- [ ] Toast appears top-right, dismissible, auto-dismisses after 5 seconds (configurable)
- [ ] Optional sound notification (configurable): play "ding" sound when donation received
- [ ] Sound notification respects browser permissions and mute settings
- [ ] Donation amount highlighted in green color
- [ ] Toast includes quick action: "Thank donor" link to pre-fill thank-you email (optional)
- [ ] Multiple donations don't stack infinitely: max 3 notifications on screen at once
- [ ] Notification dismisses when swiped on mobile
- [ ] Event bus implementation: use dependency injection pattern
- [ ] Event bus can be extended for other event types (future-proof)
- [ ] Unit tests: verify event emission and handling

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: create donation, verify notification
- [ ] E2E test: admin dashboard open, create donation via API, verify notification appears
- [ ] Sound notification tested across browsers
- [ ] Mobile notification behavior tested
- [ ] Accessibility audit passed (sound not required, visual indication enough)
- [ ] Deployed to staging and verified

## Technical Notes
- Use domain event pattern for loose coupling
- Emit event in donation service after successful transaction
- Implement event bus with listeners pattern (PubSub)
- Consider using Celery for async event processing if needed
- Store events for audit trail
- Consider email notification to admin as well (separate concern)

## Story Points: 5
