---
story: S3
epic: EPIC-82
ticket: RAP-553
title: "Admin content editor"
status: ready
points: 8
priority: P0
track: Frontend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S3: Admin content editor

## Story
As an **admin/editor**, I want **a visual content editor interface** so that **I can manage all site content without technical knowledge**.

## Description
Build a comprehensive admin interface at /admin/content to create, edit, delete, and preview content blocks. Support different editor types: rich text for long content, JSON for structured data, and live preview.

## Acceptance Criteria
- [ ] /admin/content page displays all content blocks grouped by page (home, about, volunteer, foster sections visible in sidebar)
- [ ] Content blocks listed in table with columns: page_key, language, is_published status, last updated date, updated_by user
- [ ] Click any block to open detail editor modal/page
- [ ] Editor UI includes: title field, language selector (es/en toggle), content editor, publish toggle, save/cancel buttons
- [ ] Text blocks (home_hero, home_testimonials, about_history) use rich text editor (Slate, Tiptap, or similar) with formatting: bold, italic, underline, headings, lists, links
- [ ] JSON blocks (home_team member array, home_testimonials array) use Monaco or JSON editor with validation and syntax highlighting
- [ ] Live preview panel shows how content will appear on the actual page (beside editor, 50/50 split on desktop)
- [ ] Preview updates in real-time as user types (debounced at 500ms)
- [ ] Save button sends PUT request to /api/admin/content/blocks/{id}, shows success toast "Saved successfully" and error toast if it fails
- [ ] Create button on page opens blank editor modal, auto-populated with default language (es)
- [ ] Delete button shows confirmation dialog "This content will be removed. Continue?" before deletion
- [ ] Publish toggle is visible and changes is_published flag (affects GET /api/content endpoints)
- [ ] Unpublished blocks show "DRAFT" badge in list
- [ ] Page is responsive: full editor on desktop, stacked layout on mobile
- [ ] Loading states: show skeleton while fetching blocks, loading spinner while saving
- [ ] Undo/redo buttons for recent changes (up to 10 changes per session)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for components)
- [ ] Integration test: navigate to /admin/content, edit a block, verify save
- [ ] E2E test: complete workflow (create, edit, preview, delete)
- [ ] Accessibility audit passed (WCAG 2.1 AA)
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Deployed to staging and verified

## Technical Notes
- Use React hooks for state management
- Consider Zustand or Redux for complex state
- Integrate rich text editor (TipTap recommended for flexibility)
- Use React JSON Schema Form or custom JSON editor
- Implement debounced preview updates to avoid excessive re-renders
- Add optimistic updates for save action (show success immediately, revert on error)
- Track editor dirty state to warn on unsaved changes (beforeunload)

## Story Points: 8
