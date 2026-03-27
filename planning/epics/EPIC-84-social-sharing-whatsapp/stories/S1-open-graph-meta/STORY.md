---
story: S1
epic: EPIC-84
ticket: RAP-566
title: "Open Graph meta tags for all public pages"
status: ready
points: 5
priority: P0
track: Frontend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S1: Open Graph meta tags for all public pages

## Story
As a **user sharing content**, I want **rich preview cards to appear when I share links** so that **others see appealing summaries before clicking**.

## Description
Implement dynamic Open Graph (OG) meta tags on all public pages. When shared on social media, links unfurl with title, description, and image. Use Next.js generateMetadata for dynamic tag generation.

## Acceptance Criteria
- [ ] Open Graph meta tags implemented for all public pages: /animals/{id}, /campaigns/{id}, /rescuers/{slug}, /stories, /stories/{id}, /news, /news/{slug}, homepage
- [ ] /animals/{id} page: og:title = "[Name], [Species]", og:description = "[Breed], [Age], seeking adoption", og:image = primary animal photo
- [ ] /campaigns/{id} page: og:title = "[Campaign Title]", og:description = "[Goal] - [Current Progress]%", og:image = campaign featured image
- [ ] /rescuers/{slug} page: og:title = "[Name], Rescuer", og:description = "[Bio excerpt]", og:image = rescuer profile photo
- [ ] /stories page: og:title = "Success Stories", og:description = "Inspiring adoption stories from our community", og:image = static image
- [ ] /stories/{id} page: og:title = "[Story Title]", og:description = "[Story excerpt]", og:image = story photo
- [ ] /news page: og:title = "News & Updates", og:description = "Latest news from Refugio", og:image = latest post featured image
- [ ] /news/{slug} page: og:title = "[Post Title]", og:description = "[Post excerpt]", og:image = post featured image
- [ ] All OG tags include: og:url (canonical URL), og:type (website|article), og:site_name, og:locale (es_ES or en_US)
- [ ] Twitter Card meta tags also implemented: twitter:card (summary_large_image), twitter:title, twitter:description, twitter:image
- [ ] Images optimized: OG images should be 1200x630 minimum for Facebook (16:9 ratio)
- [ ] Use Next.js generateMetadata function for dynamic tag generation
- [ ] Fallback og:image for pages without specific image (default Refugio logo)
- [ ] Tested with Facebook Sharing Debugger: og:image correctly unfurls
- [ ] Tested with Twitter Card Validator
- [ ] SEO best practice: include canonical URL in head tags
- [ ] Internationalization: og:locale changes based on page language (es_ES for /es/*, en_US for /en/*)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for metadata generation)
- [ ] Integration test: verify meta tags present on pages
- [ ] Facebook Sharing Debugger test: all pages unfurl correctly
- [ ] Twitter Card Validator test: cards display properly
- [ ] Responsive image testing: ensure og:image URLs return correct dimensions
- [ ] Deployed to staging and verified

## Technical Notes
- Use Next.js generateMetadata from next/head or page.tsx metadata export
- Consider Vercel OG library for dynamic image generation
- Ensure og:image URLs are absolute (not relative)
- Cache metadata generation for performance
- Monitor meta tag rendering with browser DevTools

## Story Points: 5
