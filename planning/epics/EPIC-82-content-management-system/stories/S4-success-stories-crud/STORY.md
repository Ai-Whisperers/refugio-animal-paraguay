---
story: S4
epic: EPIC-82
ticket: RAP-554
title: "Success stories CRUD"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S4: Success stories CRUD

## Story
As an **admin**, I want **to manage adoption success stories** so that **I can inspire potential adopters with real examples**.

## Description
Create a SuccessStory model and CRUD interface. Stories showcase adoption successes with animal details, adopter name, story text, and featured photo. Public page displays published stories with pagination.

## Acceptance Criteria
- [ ] SuccessStory model created with fields: id (UUID), title (string), animal_id (FK to Animal, nullable), adopter_name (string), story_text (text), quote (text, optional), photo_url (string), published_at (datetime, nullable), is_featured (bool), created_at (datetime), updated_at (datetime)
- [ ] Database migration with indexes on published_at, is_featured, created_at
- [ ] POST /api/admin/stories endpoint creates new story (auth: admin/editor)
- [ ] GET /api/admin/stories endpoint lists all stories with pagination (20 per page, show unpublished)
- [ ] GET /api/stories endpoint returns published stories only, sorted by published_at DESC, with pagination
- [ ] GET /api/stories/{id} endpoint returns single story detail
- [ ] PUT /api/admin/stories/{id} endpoint updates story
- [ ] DELETE /api/admin/stories/{id} endpoint deletes story (soft delete)
- [ ] /admin/stories page displays list of all stories in table format with columns: title, animal, adopter_name, published status, featured flag, created_date
- [ ] Admin can create/edit/delete stories from UI with form: title, animal selector (dropdown with search), adopter name, story text (rich text), quote, photo upload, publish toggle, featured toggle
- [ ] /stories public page shows success stories grid (3 columns on desktop, 1 on mobile) with photo, title, and "Read story" link
- [ ] Pagination at bottom with 6 stories per page
- [ ] Featured stories appear first in list
- [ ] Story detail page (/stories/{id}) shows full story with large photo, quote pull-out, adopter name, animal details link
- [ ] Share buttons on detail page (WhatsApp, Facebook, Twitter, copy link)
- [ ] API returns proper validation errors and HTTP status codes

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for CRUD operations
- [ ] E2E test: create story, publish, verify on public page
- [ ] Soft delete tested
- [ ] Deployed to staging and verified

## Technical Notes
- Use animal_id FK to show "Adopted: [Animal Name]" in story card
- Implement pagination with limit/offset
- Add search/filter by adopter_name on admin page
- Soft delete with is_deleted flag
- Consider caching GET /stories response (5 minute TTL)

## Story Points: 5
