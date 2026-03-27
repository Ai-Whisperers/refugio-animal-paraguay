---
story: S6
epic: EPIC-82
ticket: RAP-556
title: "Featured animals on homepage"
status: ready
points: 3
priority: P1
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S6: Featured animals on homepage

## Story
As an **admin**, I want **to feature specific animals on the homepage** so that **I can highlight animals most needing adoption**.

## Description
Add is_featured boolean flag to Animal model. Admins can toggle "Feature on homepage" in animal edit form. Homepage carousel displays up to 6 featured animals with rotating display.

## Acceptance Criteria
- [ ] is_featured boolean column added to Animal model (default: false)
- [ ] Database migration for is_featured column with index
- [ ] GET /api/animals?featured=true&limit=6 endpoint returns featured animals sorted by created_at DESC (most recent featured first)
- [ ] /admin/animals/{id}/edit form includes "Feature on homepage" toggle switch (prominent, near top of form)
- [ ] Toggling feature sends PATCH /api/admin/animals/{id} with {"is_featured": true|false}
- [ ] Homepage has "Featured Animals" carousel section displaying 6 featured animals
- [ ] Carousel shows large photo, animal name, species/breed, brief description (first 100 chars)
- [ ] Carousel auto-rotates every 5 seconds (slide transition with fade or slide animation)
- [ ] Manual navigation: previous/next arrow buttons on desktop, swipe on mobile
- [ ] Click animal card links to detail page (/animals/{id})
- [ ] If fewer than 6 featured animals exist, display all available without empty slots
- [ ] If no featured animals exist, show "No featured animals yet" placeholder or hide section
- [ ] Admin page shows "featured" badge/icon on animal cards that are featured
- [ ] Carousel is responsive: full-width on mobile, centered max-width on desktop
- [ ] Performance: carousel component memoized to prevent unnecessary re-renders

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for feature toggle
- [ ] E2E test: feature animal, verify on homepage carousel
- [ ] Carousel animations tested across browsers
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Deployed to staging and verified

## Technical Notes
- Use React useState for carousel current index
- Implement auto-rotation with setInterval (clear on unmount)
- Consider react-spring for smooth animations
- Add accessibility: ARIA labels for carousel, keyboard navigation (arrow keys)
- Cache GET /animals?featured=true response (1 minute TTL)

## Story Points: 3
