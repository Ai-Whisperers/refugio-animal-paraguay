---
story: S5
epic: EPIC-78
ticket: RAP-521
title: "Admin requirement configuration UI"
status: ready
points: 5
priority: P1
track: Frontend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S5: Admin requirement configuration UI

## Story
As an **adoption administrator**, I want **to configure adoption requirements in a user-friendly interface** so that **I don't need technical knowledge to set rules**.

## Description
Create admin interface for managing adoption requirements per animal with drag-and-drop ordering and visual configuration.

## Acceptance Criteria
- [ ] /admin/animals/{animal_id}/edit page has "Adoption Requirements" tab
- [ ] Tab shows list of current requirements for animal: each row shows: requirement type (readable name), value summary, is_mandatory toggle, delete button
- [ ] Requirement rows draggable: drag to reorder (order used for form display), visual drag handle (hamburger icon)
- [ ] Add requirement button: "Add Requirement" button shows modal/dropdown to add new requirement
- [ ] Add requirement modal: select requirement_type from dropdown, configure value based on type:
  - yard_required: radio buttons (required / preferred / not_needed)
  - no_children_under: number input (age 0-18)
  - experience_required: dropdown (none / some / experienced)
  - home_type: multi-select checkboxes
  - max_hours_alone: number slider
  - other_pets_ok: multi-select checkboxes
  - housing_status: radio buttons (owned / rented)
  - income_requirement: currency input
- [ ] Mandatory toggle: toggle on each requirement row to mark as mandatory or preferred
- [ ] Description for each requirement type: helper text explaining what it means
- [ ] Save button: saves all requirements atomically (PUT /admin/animals/{animal_id}/requirements with entire list)
- [ ] Global defaults button: "Set Global Defaults" button that opens similar interface for global requirements
- [ ] Delete requirement: confirmation modal before deleting
- [ ] Undo functionality: "Undo" button to revert recent changes (if not saved)
- [ ] Preview: "Preview Questions" button shows how questions will appear to adopter
- [ ] Reorder via drag-and-drop: visual feedback (highlight on hover, drop zone visible)
- [ ] Responsive: works on tablet/desktop (not necessarily mobile, as this is admin interface)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test form state, requirement type rendering
- [ ] Component test: render requirements list
- [ ] Component test: drag-and-drop reordering works
- [ ] Component test: add requirement modal displays
- [ ] Component test: edit requirement values
- [ ] Component test: toggle mandatory/preferred
- [ ] Component test: delete with confirmation
- [ ] Integration test: save changes and verify persisted
- [ ] Integration test: preview matches form UI
- [ ] Manual testing: UX flow for adding/editing/removing requirements
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React component at pages/admin/animals/{animal_id}/requirements-tab.tsx
- Drag-and-drop: use react-beautiful-dnd or similar library
- Form state: manage array of requirements with React Hook Form or similar
- Value configuration: render different inputs per requirement_type
- API call: PUT /admin/animals/{animal_id}/requirements with body {requirements: [{type, value, is_mandatory}]}
- Global defaults: separate modal/page at /admin/adoption-requirements
- Undo: store previous state in memory, provide undo button (limited history)
- Preview: render form preview component with same logic as adopter form

## Story Points: 5
