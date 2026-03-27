---
story: S2
epic: EPIC-86
ticket: RAP-581
title: "Emergency case creation form"
status: ready
points: 5
priority: P0
track: Fullstack
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S2: Emergency case creation form

## Story
As a **rescuer**, I want **an easy form to report emergencies** so that **I can quickly get help**.

## Description
Build /portal/rescuer/emergency/new form for creating emergency cases. Simplified UI focusing on essential information. Auto-published for verified rescuers.

## Acceptance Criteria
- [ ] /portal/rescuer/emergency/new page accessible to rescuer role
- [ ] Form fields: title (text input, required, placeholder "e.g., Dog hit by car, needs surgery"), description (textarea, required, 500 char limit), animal dropdown (optional, searchable), photo uploads (1-3 photos recommended), amount_needed (number input, required, in currency), deadline (date+time picker, default 72 hours from now)
- [ ] Validation: title required (max 200), description required (max 500), amount > 0, deadline >= 24 hours from now
- [ ] Photo upload: reuse MediaUploadField component, show previews
- [ ] Amount input: currency selector (USD, PYG) or auto-detect from location
- [ ] Deadline picker: date + time, with validation (show error if > 30 days or < 24 hours)
- [ ] Submit button: "Publish Emergency" (primary color, prominent)
- [ ] Cancel button: "Discard" with confirmation
- [ ] Form auto-publishes: no approval step for verified rescuers (check rescuer.is_verified flag)
- [ ] Success: redirect to /emergencies/{id} detail page with success message "Emergency published!"
- [ ] Error: show form errors inline (under each field) and top-level error toast
- [ ] Mobile responsive: full-width inputs, stacked layout
- [ ] Accessibility: proper labels, ARIA labels for form fields, submit button has keyboard focus visible

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: fill form, submit, verify emergency created
- [ ] E2E test: navigate to form, fill out, submit, verify published
- [ ] Validation tested (all error cases)
- [ ] Responsive design verified
- [ ] Accessibility audit passed
- [ ] Deployed to staging and verified

## Technical Notes
- Use React Hook Form for form management
- Reuse photo upload component from media management
- Implement optimistic redirect after submit
- Show loading state during submission
- Consider auto-saving draft to localStorage

## Story Points: 5
