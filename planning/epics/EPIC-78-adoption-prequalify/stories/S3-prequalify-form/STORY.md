---
story: S3
epic: EPIC-78
ticket: RAP-519
title: "Pre-qualification form UI"
status: ready
points: 8
priority: P0
track: Frontend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S3: Pre-qualification form UI

## Story
As a **prospective adopter**, I want **to answer questions about my living situation** so that **I can see if I'm qualified to adopt this animal**.

## Description
Create dynamic pre-qualification form that generates questions based on animal's requirements. Form has real-time validation and visual progress indicator.

## Acceptance Criteria
- [ ] /animals/{animal_id}/pre-qualify page: shows animal name/photo at top, form below
- [ ] Form dynamically generated: fetch animal's requirements from /api/animals/{animal_id}/requirements, generate form field for each requirement
- [ ] Form fields by requirement type:
  - yard_required: radio button "Yes, I have a yard" / "No, apartment/other" / "I can arrange one"
  - no_children_under: number input "Youngest child age" (0-18) or "No children"
  - experience_required: dropdown "No experience" / "Some experience" / "Very experienced"
  - home_type: checkboxes (apartment, house, farm, townhouse)
  - max_hours_alone: slider 0-24 hours with label "Max hours alone per day"
  - other_pets_ok: checkboxes (cats, dogs, rabbits, birds, other)
  - housing_status: radio button "Own" / "Rent"
  - income_requirement: currency input with EUR, validation
- [ ] All fields have labels and help text, e.g. "Cats require at least 4 hours company per day"
- [ ] Progress bar at top showing form completion percentage
- [ ] Real-time validation: show error/warning for invalid entries (e.g. age must be 0-100)
- [ ] Visual feedback: show checkmark when field valid, red X when invalid
- [ ] Submit button labeled "Check My Qualification" (only enabled when form 100% complete)
- [ ] Accessibility: proper labels, ARIA attributes, keyboard navigation
- [ ] Responsive design: single column on mobile, form width capped at 600px on desktop
- [ ] Loading state: show spinner during qualification check
- [ ] Form remembers values if user navigates away and returns (localStorage or session state)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test form generation, validation, value handling
- [ ] Component test: form renders all requirement types correctly
- [ ] Component test: validation works for each field type
- [ ] Component test: progress bar updates correctly
- [ ] Component test: form persists values on reload
- [ ] Integration test: submit sends correct data to backend
- [ ] Accessibility test: keyboard navigation works, ARIA labels present
- [ ] Component test: responsive on mobile/tablet/desktop
- [ ] Manual testing: verify UX with various requirement combinations
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/animals/{animal_id}/pre-qualify.tsx
- Form generation: map requirement_type to React component, render dynamically
- Form library: use React Hook Form for efficient form state management
- Validation: define schema per requirement type, validate on blur and submit
- Progress: calculate (fields_with_values / total_fields) * 100
- Storage: use localStorage with key "prequal_{animal_id}_{user_id}" to persist values
- API call: POST /adoption/pre-qualify with answers dict
- Error display: show validation errors in-line under field
- Accessibility: label htmlFor="field_id", ARIA-describedby for help text
- Help text: contextual tips for each requirement type

## Story Points: 8
