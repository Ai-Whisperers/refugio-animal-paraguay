---
story: S7
epic: EPIC-82
ticket: RAP-557
title: "Featured campaigns on homepage"
status: ready
points: 3
priority: P2
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S7: Featured campaigns on homepage

## Story
As an **admin**, I want **to feature specific campaigns on the homepage** so that **I can drive donations to priority campaigns**.

## Description
Add is_featured boolean flag to Campaign model. Admins toggle "Feature on homepage" in campaign edit form. Homepage displays up to 3 featured campaigns in a grid with progress bars and donate buttons.

## Acceptance Criteria
- [ ] is_featured boolean column added to Campaign model (default: false)
- [ ] Database migration for is_featured column with index
- [ ] GET /api/campaigns?featured=true&limit=3 endpoint returns featured campaigns sorted by created_at DESC
- [ ] /admin/campaigns/{id}/edit form includes "Feature on homepage" toggle switch (prominent placement)
- [ ] Toggling feature sends PATCH /api/admin/campaigns/{id} with {"is_featured": true|false}
- [ ] Homepage has "Featured Campaigns" section displaying up to 3 featured campaigns in grid layout
- [ ] Campaign cards show: campaign image, title, brief description (first 80 chars), progress bar showing amount_raised/amount_needed, percentage and currency amounts, "Donate Now" button
- [ ] Progress bar visually fills based on percentage (green when under-funded, blue when fully funded, gold when over-funded)
- [ ] Click "Donate Now" links to campaign detail page with donate button focused
- [ ] If fewer than 3 featured campaigns exist, display all available
- [ ] If no featured campaigns exist, show placeholder or hide section
- [ ] Admin animals page shows "featured" icon on campaign cards
- [ ] Grid is responsive: 3 columns on desktop, 2 on tablet, 1 on mobile
- [ ] Campaign cards have consistent height and alignment (CSS grid)
- [ ] Performance: campaign section memoized to prevent unnecessary re-renders

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for feature toggle
- [ ] E2E test: feature campaign, verify on homepage
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Deployed to staging and verified

## Technical Notes
- Reuse progress bar component from campaign detail page
- Use CSS Grid for responsive layout
- Cache GET /campaigns?featured=true response (1 minute TTL)
- Add accessibility: alt text for images, proper heading hierarchy

## Story Points: 3
