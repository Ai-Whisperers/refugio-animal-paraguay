---
story: S6
epic: EPIC-83
ticket: RAP-564
title: "Campaign and story image uploads"
status: ready
points: 3
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S6: Campaign and story image uploads

## Story
As an **admin**, I want **to attach images to campaigns, success stories, and blog posts** so that **content is visually appealing and engaging**.

## Description
Integrate image upload into campaign creation/edit, success story forms, and blog post forms. Each uses the existing /media/upload endpoint with image field upload.

## Acceptance Criteria
- [ ] Campaign create/edit form includes image upload field: "Campaign Image"
- [ ] Campaign form accepts jpg, png, webp (validated via upload endpoint)
- [ ] Campaign model has featured_image_id (FK to Media)
- [ ] Success story form includes image upload field: "Story Photo"
- [ ] Story model has photo_id (FK to Media)
- [ ] Blog post form includes image upload field: "Featured Image"
- [ ] BlogPost model has featured_image_id (FK to Media)
- [ ] All upload fields use same drag-and-drop UI component (reusable MediaUploadField component)
- [ ] Upload field shows preview of selected image while editing form
- [ ] Clear/remove button allows changing image after selection
- [ ] Form submission sends image to POST /api/media/upload first, then creates/updates entity with returned media_id
- [ ] Optimistic updates: show preview immediately while upload completes
- [ ] Error handling: show toast if upload fails, allow retry
- [ ] Images are required for: campaign (except maybe internal campaigns), story (required), blog post (optional)
- [ ] On form load, existing image is displayed as preview
- [ ] All three forms responsive on mobile (full-width upload field)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for component)
- [ ] Integration test: upload image in campaign form, verify stored
- [ ] E2E test: complete campaign creation with image upload
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Deployed to staging and verified

## Technical Notes
- Create reusable MediaUploadField component (used in animal gallery, campaign, story, blog)
- Implement with react-dropzone for consistency
- Add image preview using optimized thumbnail URL
- Show upload progress bar during upload
- Implement error retry logic

## Story Points: 3
