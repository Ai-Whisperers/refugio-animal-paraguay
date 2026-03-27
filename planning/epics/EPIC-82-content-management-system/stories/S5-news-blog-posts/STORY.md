---
story: S5
epic: EPIC-82
ticket: RAP-555
title: "News/blog posts"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S5: News/blog posts

## Story
As an **admin**, I want **to publish news and blog posts** so that **I can share updates and engage the community**.

## Description
Create BlogPost model supporting articles with rich HTML content. Posts are published on /news page with individual detail pages at /news/{slug}. Homepage shows latest 3 posts. Admin interface for CRUD operations.

## Acceptance Criteria
- [ ] BlogPost model created with fields: id (UUID), title (string), slug (string, unique), body_html (text), author_id (FK to User), published_at (datetime, nullable), is_published (bool), featured_image_url (string), tags (JSON array), created_at (datetime), updated_at (datetime)
- [ ] Database migration with indexes on slug, published_at, is_published, created_at
- [ ] POST /api/admin/blog endpoint creates new post (auth: admin/editor), auto-generates slug from title (slugify)
- [ ] GET /api/admin/blog endpoint lists all posts with pagination (20 per page)
- [ ] GET /api/blog endpoint returns published posts only, sorted by published_at DESC, with pagination (10 per page)
- [ ] GET /api/blog/{slug} endpoint returns single post detail with related posts (last 3 by tag)
- [ ] PUT /api/admin/blog/{id} endpoint updates post, allows slug override
- [ ] DELETE /api/admin/blog/{id} endpoint deletes post (soft delete)
- [ ] /admin/blog page displays table of all posts: title, author, tags, published status, publish date, created date
- [ ] Admin create/edit form: title, slug (optional, auto-generated), featured image upload, body (rich HTML editor), tags (multi-select or comma-separated input), author (auto-filled from current user), publish date picker, publish toggle
- [ ] /news public page displays blog posts grid (2 columns on desktop, 1 on mobile) with featured image, title, excerpt (first 150 chars), author name, publish date, "Read more" button
- [ ] Pagination at bottom with 10 posts per page
- [ ] /news/{slug} detail page shows full post with featured image, title, author info, publish date, body HTML rendered, tags as clickable links
- [ ] Tag page /news/tag/{tag} shows all posts with that tag
- [ ] Homepage shows latest 3 published posts in "Recent News" section with featured image, title, excerpt, link to full post
- [ ] Slug collision detection: if slug exists, append -2, -3, etc.
- [ ] Proper escaping of user input in HTML rendering

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for CRUD operations
- [ ] E2E test: create post, publish, verify on /news page and homepage
- [ ] XSS prevention tested (input sanitization)
- [ ] Deployed to staging and verified

## Technical Notes
- Use rich text editor (TipTap, Slate) and export as HTML
- Implement slug generation with collision handling
- Add excerpt auto-generation if not provided
- Consider markdown support as alternative to HTML
- Cache GET /blog responses (5 minute TTL)
- Use react-markdown or DOMPurify for safe HTML rendering

## Story Points: 5
