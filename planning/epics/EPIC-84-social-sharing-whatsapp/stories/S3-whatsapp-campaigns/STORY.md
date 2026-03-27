---
story: S3
epic: EPIC-84
ticket: RAP-568
title: "WhatsApp share for campaigns"
status: ready
points: 3
priority: P0
track: Frontend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S3: WhatsApp share for campaigns

## Story
As a **supporter**, I want **to share campaigns on WhatsApp** so that **I can ask friends to donate to important causes**.

## Description
Add WhatsApp share button to campaign detail pages with messages tailored to campaign type (fundraising or castration). Message includes progress and call-to-action.

## Acceptance Criteria
- [ ] WhatsApp share button appears on campaign detail page (top right or alongside other share buttons)
- [ ] Share button icon uses WhatsApp logo/SVG with hover tooltip "Share on WhatsApp"
- [ ] For general fundraising campaigns: message format "Ayudanos a alcanzar nuestra meta! Ya logramos [X]% [campaign_title]. [full_url]"
- [ ] Example: "Ayudanos a alcanzar nuestra meta! Ya logramos 45% Castration Campaign 2026. https://refugio.app/campaigns/xyz789"
- [ ] For castration campaigns: message format "Ya castramos [X] animales! Ayudanos a llegar a [Y] [campaign_title]. [full_url]"
- [ ] Example: "Ya castramos 120 animales! Ayudanos a llegar a 200 Castration Campaign 2026. https://refugio.app/campaigns/xyz789"
- [ ] Campaign type detection: look for "castration" in title/category or specific campaign_type field
- [ ] Message properly URL-encoded for WhatsApp
- [ ] Opening WhatsApp app on mobile (native or web fallback)
- [ ] Button accessible and responsive on all device sizes
- [ ] ARIA labels for accessibility
- [ ] Clicking button tracks share event (for S5 analytics)
- [ ] Works on iOS and Android

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: click button, verify message construction
- [ ] Manual testing on iOS and Android
- [ ] Accessibility audit passed
- [ ] Responsive design verified
- [ ] Deployed to staging and verified

## Technical Notes
- Detect campaign type: check campaign_type field or keywords in title
- Build messages dynamically with campaign data: amount_raised, amount_needed
- Use same WhatsApp share component as animal cards
- Message construction: encodeURIComponent(`Ayudanos a alcanzar nuestra meta! Ya logramos ${percentage}% ${campaign.title}. ${url}`)
- Track share action in S5 analytics

## Story Points: 3
