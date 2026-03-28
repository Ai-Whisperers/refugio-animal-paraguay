---
story: S5
epic: EPIC-85
ticket: RAP-577
title: "Admin real-time activity feed"
status: done
points: 5
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S5: Admin real-time activity feed

## Story
As an **admin**, I want **to see real-time activity on my dashboard** so that **I can monitor important events**.

## Description
Add real-time activity feed to /admin/dashboard showing recent events: donations, adoptions, animal registrations, campaign milestones. Uses Server-Sent Events (SSE) for live updates.

## Acceptance Criteria
- [ ] GET /admin/activity/stream SSE endpoint created (auth: admin role)
- [ ] Endpoint broadcasts events: new donation (amount, donor name), new adoption application (animal, applicant), new animal registered (name, species), campaign milestone (amount reached, campaign name), medical alert (animal, alert type)
- [ ] Activity Feed component shows last 20 events in reverse chronological order
- [ ] Each event shows: event type icon, brief description, timestamp (relative: "2 minutes ago")
- [ ] Events update in real-time as they occur (SSE push)
- [ ] Fallback to polling every 10 seconds if SSE not supported
- [ ] Activity feed is pageable: "Load more" button shows older events (20 per page)
- [ ] Activity feed is filterable: filter by event type (donation, adoption, animal, campaign, medical)
- [ ] Click event shows more details in modal or detail page
- [ ] Activity events have icons: green checkmark for adoption, money icon for donation, plus icon for animal, alert icon for medical alert
- [ ] Mobile responsive: full-width feed, stacked event cards
- [ ] Accessibility: proper semantic HTML, ARIA live region for real-time updates

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for component)
- [ ] Integration test: emit events, verify feed displays
- [ ] E2E test: navigate to dashboard, observe real-time events
- [ ] SSE tested across browsers
- [ ] Fallback polling behavior tested
- [ ] Responsive design verified
- [ ] Accessibility audit passed
- [ ] Deployed to staging and verified

## Technical Notes
- Use Server-Sent Events (SSE) for real-time push from server
- Implement fallback to polling for browsers not supporting SSE
- Use event sourcing pattern for activity events
- Store events in database for history
- Consider using Redis Pub/Sub for scaling across multiple servers
- Implement connection management: reconnect on disconnect, max retry backoff

## Story Points: 5
