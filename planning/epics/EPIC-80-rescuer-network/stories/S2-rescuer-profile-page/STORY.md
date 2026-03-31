---
story: S2
epic: EPIC-80
ticket: RAP-534
title: "Rescuer profile page"
status: done
points: 8
priority: P0
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S2: Rescuer profile page

## Story
As a **potential donor**, I want **to see rescuer's profile** so that **I can decide to support them**.

## Description
Create public rescuer profile page showing bio, animals, campaigns, impact stats, and donor wall with support button.

## Acceptance Criteria
- [ ] /rescuers/{slug} page: shows rescuer profile with: display name, photo (if available), bio, location, verification badge
- [ ] Impact section: shows: "X animals rescued", "X adopted out", "X castrated", "X supported financially"
- [ ] Animals section: links to/lists rescue animals in care with photos, names, adoption status
- [ ] Campaigns section: shows campaigns created by rescuer with progress
- [ ] Donor wall: shows supporters with amounts (respect anonymity preferences), "X people supporting"
- [ ] Support button: "Support This Rescuer" button with donation options: one-time or monthly
- [ ] Contact section: email/WhatsApp links (if provided), messaging option
- [ ] Social links: Facebook, Instagram links if provided
- [ ] Verification badge: displays if rescuer is verified with method indicator
- [ ] Responsive design: single column on mobile, multi-column on desktop
- [ ] Share functionality: share buttons to social media

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test page rendering
- [ ] Component test: profile renders correctly with all sections
- [ ] Component test: responsive on mobile/tablet/desktop
- [ ] Integration test: fetch rescuer data and display
- [ ] Integration test: support button works
- [ ] Manual testing: verify UX
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/rescuers/{slug}.tsx
- Profile data: GET /api/rescuers/{slug}
- Responsive: Tailwind CSS responsive utilities

## Story Points: 8
