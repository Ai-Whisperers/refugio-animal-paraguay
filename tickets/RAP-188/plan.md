# RAP-188 Plan

## Objective
When staff marks a task as completed, prompt for optional completion notes, and display completion notes on the task card.

## Description
The backend already stores completion_notes and auto-sets completed_at (RAP-185). This story surfaces that in the frontend: a "Complete Task" modal with a notes field, and notes display on completed cards.

## Acceptance Criteria
- [ ] Moving task to "Completado" opens a confirmation modal with optional notes field
- [ ] Completion notes (if entered) are sent to PATCH /api/tasks/{id}
- [ ] Completed task card shows the completion notes below the completion timestamp
- [ ] Empty state handled (no notes entered = null sent)
- [ ] Error surfaced if PATCH fails

## Complexity Assessment
**Track**: Simple Fix — single file change to tasks/page.tsx

## Approach
1. Intercept "Completado" selection in the status dropdown
2. Open CompleteTaskModal with notes field
3. On submit: PATCH { status: "completed", completion_notes: notesText | null }
4. Update local state including completion_notes
5. Display notes on card

## Dependencies
- Depends on: RAP-187 (tasks page exists with assignment support)
