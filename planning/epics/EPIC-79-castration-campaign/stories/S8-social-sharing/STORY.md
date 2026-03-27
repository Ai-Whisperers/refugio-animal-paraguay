---
story: S8
epic: EPIC-79
ticket: RAP-532
title: "Social media sharing with auto-generated cards"
status: ready
points: 2
priority: P2
track: Frontend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S8: Social media sharing with auto-generated cards

## Story
As a **campaign supporter**, I want **to share campaign progress on social media** so that **I can inspire others to donate**.

## Description
Add social media share buttons with auto-generated preview cards showing campaign statistics and impact.

## Acceptance Criteria
- [ ] Campaign page share buttons: WhatsApp, Facebook, Twitter, LinkedIn buttons
- [ ] WhatsApp share: pre-filled message "We've castrated X animals! Help us reach Y. Support here: [link]" with emoji/formatting
- [ ] Facebook share: uses Open Graph meta tags for rich preview (image, title, description)
- [ ] Twitter share: pre-filled text "Check out our castration campaign - X animals treated! Support us: [link]"
- [ ] Image card generation: auto-create image showing: campaign name, "X of Y animals castrated", progress percentage, clinic logos, call to action
- [ ] Image update: regenerate image whenever completed_count changes (use image service or cached image with dynamic overlay)
- [ ] Open Graph tags: set on campaign page: og:title, og:description, og:image (auto-generated card), og:url
- [ ] Fallback image: if dynamic generation fails, use default campaign image

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test share URL generation
- [ ] Component test: share buttons render correctly
- [ ] Component test: share URLs are correct
- [ ] Manual testing: verify shares work on WhatsApp, Facebook, Twitter
- [ ] Manual testing: verify preview cards display correctly
- [ ] Deployed to staging and verified

## Technical Notes
- Share buttons: use social-share-button or hand-craft URLs
- Image generation: use PIL/Pillow or external image generation service
- Dynamic overlay: if progress changes, regenerate image or use client-side overlay
- Open Graph: set meta tags in Next.js head
- WhatsApp encoding: URL encode special characters in message
- URL shortening: optional, use bit.ly or similar for sharing

## Story Points: 2
