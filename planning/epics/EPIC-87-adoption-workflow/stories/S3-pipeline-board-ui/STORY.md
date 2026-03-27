---
story: S3
epic: EPIC-87
ticket: RAP-590
title: "Adoption pipeline board UI"
status: ready
points: 8
priority: P0
track: Frontend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S3: Adoption pipeline board UI

## Story
As an **adoption coordinator**, I want **a Kanban board view of adoptions** so that **I can visually manage the pipeline**.

## Description
Create /admin/adoptions/pipeline page with Kanban-style board. Columns represent adoption stages. Cards show applications and can be dragged between columns.

## Acceptance Criteria
- [ ] /admin/adoptions/pipeline page loads all adoptions and stages
- [ ] Kanban board with columns per stage (configurable from S1)
- [ ] Cards display in columns sorted by created_at (oldest first)
- [ ] Each card shows: applicant name, animal name, days in current stage, urgency flag if past timeout
- [ ] Card styling: light colored background, larger text for key info, color-coded by urgency (green, yellow, red)
- [ ] Drag card between columns to move adoption to next/previous stage
- [ ] Drag-and-drop triggers PATCH /api/admin/adoptions/{id}/advance API call
- [ ] Drop invalid (moving to non-adjacent stage) shows error toast
- [ ] Click card opens adoption detail modal or page with full information
- [ ] Detail modal includes: applicant info, animal, current stage, history, action buttons
- [ ] Filter controls: filter by animal, stage, applicant name, date range
- [ ] Search box: search by applicant name or animal name
- [ ] Sorting options: by date, by applicant name, by animal
- [ ] Board view scrolls horizontally if many stages (mobile)
- [ ] Timeout indicators: red "OVERDUE" badge if days_in_stage exceeds timeout_days
- [ ] Responsive: single column on mobile (vertical scrolling), full Kanban on desktop
- [ ] Accessibility: keyboard navigation, ARIA labels, screen reader friendly
- [ ] Performance: virtualize columns if many cards (lazy load)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage for component)
- [ ] Integration test: fetch adoptions, verify board displays
- [ ] E2E test: drag card between columns, verify API called
- [ ] Drag-and-drop tested across browsers
- [ ] Responsive design verified
- [ ] Accessibility audit passed
- [ ] Performance verified (no lag with 100+ cards)
- [ ] Deployed to staging and verified

## Technical Notes
- Use React Beautiful DnD or react-dnd for drag-and-drop
- Fetch adoptions with stage info: GET /api/admin/adoptions?status=all
- Implement optimistic updates for drag-and-drop
- Cache stages for filtering options
- Add loading skeleton while fetching
- Monitor performance with React DevTools Profiler

## Story Points: 8
