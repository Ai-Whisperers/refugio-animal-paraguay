---
story: S8
epic: EPIC-82
ticket: RAP-558
title: "Multilingual content support"
status: ready
points: 5
priority: P2
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S8: Multilingual content support

## Story
As a **Spanish-speaking user**, I want **all content to be available in Spanish** so that **I can use the platform in my native language**.

## Description
Extend content management system to fully support multiple languages (Spanish and English). Content blocks, stories, blog posts all have language-specific versions. API accepts ?lang parameter, frontend passes current locale.

## Acceptance Criteria
- [ ] ContentBlock model already supports language field (Spanish and English)
- [ ] SuccessStory model extended with language field (es, en) - default es
- [ ] BlogPost model extended with language field (es, en) - default es
- [ ] Database indexes added on (entity_id, language) for efficient queries
- [ ] GET /api/content/blocks?lang=es|en parameter filters by language
- [ ] GET /api/stories?lang=es|en parameter filters by language
- [ ] GET /api/blog?lang=es|en parameter filters by language
- [ ] Frontend passes current locale to all content endpoints (stored in Next.js i18n context or localStorage)
- [ ] /admin/content editor shows side-by-side es/en editing tabs for content blocks
- [ ] Admin can edit Spanish and English versions independently
- [ ] Admin can mark translation as "pending" (auto-filled from Spanish if missing)
- [ ] Admin view shows translation progress: "[2/3 languages completed]" badge
- [ ] If translation missing for requested language, API returns Spanish version as fallback with language_fallback: true flag in response
- [ ] Frontend respects fallback: shows content in original language if translation missing
- [ ] Language selector on public site (top right header) allows es/en toggle
- [ ] Changing language refreshes all content sections with translated versions
- [ ] URL updates to reflect language (consider /es/stories vs /stories with Accept-Language header)
- [ ] Blog post and success story detail pages show available language versions with links to switch

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for language filtering and fallback
- [ ] E2E test: create bilingual content, toggle language on site, verify both versions display
- [ ] All public pages tested in both Spanish and English
- [ ] Translated content displays correctly without formatting issues
- [ ] Deployed to staging and verified

## Technical Notes
- Use Next.js built-in i18n routing (next-i18n-router) or similar
- Store language preference in localStorage and/or URL
- Consider SEO implications (hreflang tags for each language)
- Use i18next or similar library for client-side translations
- Add migration to create Spanish/English versions of existing content
- Implement translation status tracking for admins

## Story Points: 5
