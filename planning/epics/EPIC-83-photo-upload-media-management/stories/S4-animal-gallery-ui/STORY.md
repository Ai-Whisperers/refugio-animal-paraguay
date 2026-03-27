---
story: S4
epic: EPIC-83
ticket: RAP-562
title: "Animal photo gallery management UI"
status: ready
points: 5
priority: P1
track: Frontend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S4: Animal photo gallery management UI

## Story
As an **admin**, I want **to manage photos for each animal** so that **I can showcase animals with multiple high-quality images**.

## Description
Build gallery management interface on animal edit page. Staff can drag-and-drop to reorder photos, set primary photo, delete, and upload new photos with progress feedback.

## Acceptance Criteria
- [ ] /admin/animals/{id}/edit page includes "Photos" section with gallery management
- [ ] Gallery displays thumbnails of all animal photos in grid layout (4 columns on desktop, 2 on tablet, 1 on mobile)
- [ ] Drag-and-drop to reorder photos: grab thumbnail and drag to new position, updates ordering
- [ ] Reordering sends PATCH /api/admin/animals/{id}/photos/order with array of photo IDs in new order
- [ ] Primary photo selector: star icon on each thumbnail, clicking makes that photo primary (first in list)
- [ ] Delete button on each thumbnail: click shows confirmation "Delete this photo?" before removing
- [ ] Delete sends DELETE /api/admin/animals/{id}/photos/{photo_id}
- [ ] Upload zone: drag-and-drop area accepts image files, or click to select files
- [ ] Multiple file selection supported (select up to 10 files at once)
- [ ] Upload progress bar shown per file with percentage and file name
- [ ] On upload complete, new photos appear in gallery automatically
- [ ] Validation: show error toast if file too large (>10MB) before uploading
- [ ] Empty state: if no photos, show "No photos yet. Drag photos here or click to upload."
- [ ] Photos are AnimalPhoto model: animal_id FK, media_id FK, order (int), is_primary (bool), created_at
- [ ] Primary photo is displayed first in animal detail page and on animal cards in catalog
- [ ] Gallery section collapsible for easier form navigation
- [ ] Accessibility: ARIA labels for buttons, keyboard navigation support
- [ ] Performance: limit photo display to 100 (unlikely but worth handling)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for components)
- [ ] Integration test: upload photos, reorder, set primary, delete
- [ ] E2E test: complete gallery workflow
- [ ] Drag-and-drop tested across browsers
- [ ] Accessibility audit passed
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Deployed to staging and verified

## Technical Notes
- Use React Beautiful DnD or react-dnd for drag-and-drop
- Implement optimistic updates for better UX
- Show loading skeleton while uploading
- Use React Dropzone for drag-and-drop upload zone
- Implement chunked uploads for large files if needed
- Add loading state to prevent double-submission during upload

## Story Points: 5
