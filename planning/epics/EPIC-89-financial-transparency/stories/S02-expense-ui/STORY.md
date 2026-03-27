---
story: S2
epic: EPIC-89
ticket: RAP-605
title: "Expense management UI with receipts"
status: ready
points: 5
priority: P0
track: Frontend
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S02: Expense Recording UI with Receipt Upload

## Story

As an admin, I want a user-friendly interface to record expenses with receipt photos so that I can quickly log spending without switching between multiple systems.

## Description

Build admin expense recording form at /admin/expenses with receipt image upload capability. Display expense list with filtering and sorting. Implement approve/reject workflow with admin controls.

## Acceptance Criteria

- [ ] Create /admin/expenses page with two sections: "Add Expense" form and "Recent Expenses" list
- [ ] Add Expense form fields:
  - [ ] Amount (number input with currency selector: PYG, USD, EUR)
  - [ ] Category (dropdown: medical, food, shelter, rescue, operations, transport, admin)
  - [ ] Description (text area, required)
  - [ ] Date (date input, default today, cannot be future)
  - [ ] Receipt photo (file upload button)
- [ ] Receipt upload: "Cargar recibo" button, accept image/* types only
- [ ] Receipt preview: show thumbnail after upload (max 200x200px)
- [ ] Receipt upload progress: show "Subiendo..." during upload
- [ ] Handle upload errors: "Error al cargar recibo" with retry button
- [ ] Form validation: show errors for missing required fields
- [ ] Submit button: "Guardar gasto" (Save expense)
- [ ] Show success message "Gasto registrado" after save
- [ ] Clear form after successful submission
- [ ] Recent Expenses list:
  - [ ] Columns: Date, Category badge, Amount (with currency), Description, Status badge, Actions
  - [ ] Status badge colors: pending (yellow), approved (green), rejected (red)
  - [ ] Sortable columns: date, amount, status
- [ ] Filter options:
  - [ ] Category dropdown (multi-select)
  - [ ] Status filter (pending, approved, rejected, all)
  - [ ] Date range: "From" and "To" date inputs
- [ ] Table pagination: show 20 expenses per page
- [ ] Action buttons for each expense:
  - [ ] View details (icon)
  - [ ] Edit (icon) - only if pending
  - [ ] Delete (icon) - only if pending
  - [ ] Approve (button) - only if pending
  - [ ] Reject (button) - only if pending
- [ ] Approve action: instantly approve (no confirm dialog needed)
- [ ] Reject action: show modal with reason textarea, submit rejects
- [ ] Expense detail modal: show full expense info with large receipt preview
- [ ] Responsive layout: stacks on mobile, side-by-side on desktop

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Form validation working
- [ ] File upload functionality tested
- [ ] Receipt preview rendering correctly
- [ ] List filtering and sorting working
- [ ] Pagination tested
- [ ] Approve/reject workflow tested
- [ ] Error messages display appropriately
- [ ] Loading states show during operations
- [ ] Mobile responsive layout verified
- [ ] Integration with backend API verified
- [ ] Unit tests for form components
- [ ] E2E test for expense creation workflow
- [ ] Deployed to staging and verified

## Technical Notes

- Use React Hook Form for form state management
- Use multipart/form-data for file upload
- Implement image compression on client before upload
- Show upload progress with ProgressBar component
- Debounce filter/sort inputs for performance
- Cache expense list and invalidate on changes
- Implement optimistic updates (show approved immediately, revert if fails)
- Use Tailwind CSS for responsive styling

## Story Points: 5
