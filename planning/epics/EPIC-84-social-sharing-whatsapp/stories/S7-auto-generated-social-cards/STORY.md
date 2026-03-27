---
story: S7
epic: EPIC-84
ticket: RAP-572
title: "Auto-generated social media cards"
status: ready
points: 3
priority: P2
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S7: Auto-generated social media cards

## Story
As a **user**, I want **attractive preview cards when sharing links** so that **my shares look polished and drive more clicks**.

## Description
Create dynamic endpoint that generates PNG cards for social media unfurling. Cards show animal info, campaign progress, or story details with visual branding.

## Acceptance Criteria
- [ ] GET /og-image/{type}/{id} endpoint generates PNG dynamically (no storage, generated on-the-fly)
- [ ] Image type options: animal, campaign, story, blog
- [ ] Animal card: animal photo (primary), animal name overlaid in bold white text, "Adoptame!" text at bottom, Refugio logo watermark
- [ ] Campaign card: campaign image or progress visual, campaign title, progress bar showing raised/goal, percentage and amount, "Donate!" CTA
- [ ] Story card: story photo, story title, "Read Story" CTA, Refugio branding
- [ ] Blog card: blog featured image, blog title, author name, publish date
- [ ] Card dimensions: 1200x630 pixels (OG recommended size, 16:9 ratio)
- [ ] Generated using Pillow (PIL) for image manipulation
- [ ] Response returns PNG image with Content-Type: image/png
- [ ] Cache headers: Cache-Control: public, max-age=3600 (cache for 1 hour)
- [ ] Font rendering: use system fonts or bundled fonts (consider Pillow's ImageDraw)
- [ ] Text positioning and sizing: title, subtitle, CTA positioned for mobile preview
- [ ] Fallback: if image generation fails, return static placeholder image (Refugio logo)
- [ ] Performance: generation should complete in under 500ms per request
- [ ] Unit tests: verify image generation, correct dimensions, text content

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: generate cards for different entity types
- [ ] Generated images verified: correct dimensions, content, readability
- [ ] Performance tested: generation time under 500ms
- [ ] Browser tested: og:image renders correctly in meta preview
- [ ] Deployed to staging and verified

## Technical Notes
- Use PIL/Pillow for image generation
- Consider caching common cards (Redis) for performance
- Implement retry logic if Pillow fails (fallback to placeholder)
- Use ImageDraw for text rendering with custom fonts
- Consider third-party service for advanced design (Vercel OG, Cloudinary, etc)
- Monitor generation latency and cache hit rate

## Story Points: 3
