---
story: S2
epic: EPIC-84
ticket: RAP-567
title: "WhatsApp share buttons on animal cards"
status: ready
points: 3
priority: P0
track: Frontend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S2: WhatsApp share buttons on animal cards

## Story
As a **visitor**, I want **to share animals on WhatsApp** so that **I can recommend animals to friends quickly**.

## Description
Add WhatsApp share button to every animal card in catalog and detail pages. Clicking opens WhatsApp with pre-filled message including animal name, brief description, and link.

## Acceptance Criteria
- [ ] WhatsApp share icon appears on every animal card: in catalog grid view and detail page
- [ ] Icon uses WhatsApp logo/SVG (or text "Share on WhatsApp")
- [ ] Click opens wa.me URL with pre-filled message
- [ ] Message format: "Mira a [animal_name]! [species], [age]. Esta buscando un hogar. [full_url]"
- [ ] Example: "Mira a Max! Perro, 3 años. Esta buscando un hogar. https://refugio.app/animals/abc123"
- [ ] Message properly URL-encoded and escaped for WhatsApp
- [ ] Link opens WhatsApp app on mobile (native app or web if not installed)
- [ ] Icon positioned consistently on animal cards (bottom right corner)
- [ ] Icon hover effect: tooltip "Share on WhatsApp" or slight scale increase
- [ ] Mobile responsive: button full-width below animal card on mobile (stacked with other share buttons)
- [ ] Accessibility: proper ARIA label for screen readers
- [ ] Clicking button tracks share event (for S5 analytics)
- [ ] User doesn't need to be logged in to share
- [ ] Works on both iOS and Android (native WhatsApp integration)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: click WhatsApp button, verify URL construction
- [ ] Manual testing on mobile (iOS and Android)
- [ ] Accessibility audit passed
- [ ] Responsive design verified
- [ ] Deployed to staging and verified

## Technical Notes
- Use wa.me/{phone_id} URL scheme (no phone needed for general sharing)
- URL encode message using encodeURIComponent()
- Message: encodeURIComponent(`Mira a ${name}! ${species}, ${age}. Esta buscando un hogar. ${window.location.href}`)
- Icon component reusable across catalog, detail, featured animal carousel
- Consider tracking share as user action (S5)

## Story Points: 3
