---
story: S2
epic: EPIC-79
ticket: RAP-526
title: "Public castration campaign page with live counter"
status: ready
points: 8
priority: P0
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S2: Public castration campaign page with live counter

## Story
As a **donor**, I want **to see castration campaign progress in real-time** so that **I'm motivated to donate and see impact**.

## Description
Create public campaign page with prominent counter showing animals castrated vs target. Include clinic info, photo gallery, donation CTA, and next event date.

## Acceptance Criteria
- [ ] /campaigns/castration/{id} public page: shows campaign title prominently
- [ ] Hero section: large animated counter "X of Y animals castrated" with progress bar (percentage filled), goal: show X/Y and percentage
- [ ] Counter animation: if count increases, animate counter from old to new value
- [ ] Progress bar: visual bar showing progress from 0% to 100%, milestone markers at 25%, 50%, 75%, 100%
- [ ] Campaign goal message: motivational text from campaign.goal_message
- [ ] Clinic partners section: list all partner clinics with: name, location, logo/photo, link to clinic profile
- [ ] Photo gallery section: "Animals Helped" or "Surgery Gallery" showing before/after photos of castrated animals (with consent)
- [ ] Photo gallery: grid layout, lazy-loaded, lightbox on click, shows animal name and date
- [ ] Next drive date: prominent display of next CastrationDrive date/location if exists
- [ ] Donate button: "Support Castration Program" button redirecting to /donate/voucher with campaign pre-selected
- [ ] Date range: shows "Campaign runs until [end_date]" or "Campaign ended [end_date]"
- [ ] Impact stats: below hero, show: "Cost per surgery" (if data available), "Surgeries performed" (count), "Animals helped" (count of unique animals)
- [ ] Success messages: "We've reached X% of our goal!" every 25%
- [ ] Share section: WhatsApp, Facebook, Twitter share buttons with pre-filled messages
- [ ] Responsive design: mobile-optimized with single column layout
- [ ] Real-time updates: if possible, show live counter updates (WebSocket or polling)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test counter logic, progress calculation
- [ ] Component test: counter renders and animates correctly
- [ ] Component test: progress bar displays correctly
- [ ] Component test: photo gallery displays and loads lazily
- [ ] Component test: responsive on mobile/tablet/desktop
- [ ] Integration test: fetch campaign data and display correctly
- [ ] Integration test: donation button pre-fills campaign
- [ ] Manual testing: verify counter updates on redemption
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/campaigns/castration/{id}.tsx
- Counter animation: use framer-motion or react-spring
- Progress bar: CSS or Recharts for visual display
- Photo gallery: use lightbox library (photoswipe, react-medium-image-zoom)
- Lazy loading: IntersectionObserver for images
- Real-time updates: optional WebSocket connection to campaign updates
- Share buttons: use social-share-button library or custom implementation
- Donation CTA: navigate to /donate/voucher?campaign_id={id}
- Campaign data: GET /api/campaigns/castration/{id}

## Story Points: 8
