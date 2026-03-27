---
story: S4
epic: EPIC-84
ticket: RAP-569
title: "Social media share buttons (Facebook, Instagram, Twitter)"
status: ready
points: 3
priority: P1
track: Frontend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S4: Social media share buttons (Facebook, Instagram, Twitter)

## Story
As a **visitor**, I want **to share on major social media platforms** so that **I can reach a wider audience with Refugio content**.

## Description
Create reusable share button component with support for WhatsApp, Facebook, Twitter/X, Instagram, and native share API. Includes copy-link button for easy sharing.

## Acceptance Criteria
- [ ] Share bar component created with buttons: WhatsApp, Facebook, Share on Twitter/X, Copy Link
- [ ] Placed on: animal detail pages, campaign detail pages, success story detail pages, blog post pages
- [ ] Facebook share: opens Facebook Sharer dialog with og:url, og:title, og:image from page meta tags
- [ ] Twitter share: opens Twitter Intents share URL with predefined message and link
- [ ] Twitter message format customizable per page type (animal, campaign, story, blog)
- [ ] Copy Link button: copies current page URL to clipboard, shows "Copied!" toast message for 2 seconds
- [ ] Native share API: use navigator.share on mobile if available (opens native share sheet)
- [ ] Share buttons responsive: horizontal row on desktop, vertical stack or dropdown on mobile
- [ ] Icons: use standard social media logos or text labels ("Share on Facebook", "Share on Twitter", etc)
- [ ] Hover effects: subtle scale or color change
- [ ] ARIA labels for accessibility: "Share on Facebook", "Share on Twitter", etc
- [ ] No tracking pixel or social embed until user clicks (privacy first)
- [ ] Accessibility: keyboard navigable, screen reader friendly
- [ ] Links open in new tab/window (target="_blank")

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for component)
- [ ] Integration test: click each social button, verify URL construction
- [ ] Manual testing on iOS/Android browsers
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Deployed to staging and verified

## Technical Notes
- Facebook: https://www.facebook.com/sharer/sharer.php?u=[URL]
- Twitter: https://twitter.com/intent/tweet?url=[URL]&text=[TEXT]&hashtags=[HASHTAGS]
- Use navigator.share for native mobile sharing if available
- Implement fallback for missing social buttons
- Component props: title, description, shareUrl, hashtags
- Consider react-share library for standardized implementations

## Story Points: 3
