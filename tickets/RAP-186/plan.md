# RAP-186 Plan

## Objective
Build a Kanban-style task board for staff to view and manage volunteer tasks by status.

## Acceptance Criteria
- [ ] Admin page at /admin/tasks showing tasks in Kanban columns (Pending, In Progress, Completed, Cancelled)
- [ ] Each task card shows: title, category badge, priority indicator, assignee, due date
- [ ] Staff can change task status by moving between columns (click action)
- [ ] Filter by category and priority
- [ ] Empty state handled per column
- [ ] Loading and error states
- [ ] Navigation link in admin sidebar

## Complexity Assessment
**Track**: Complex — new admin page + API integration + Kanban UI

## Approach
1. Create `/admin/tasks/page.tsx` — Kanban board with 4 status columns
2. Create `/admin/tasks/[id]/page.tsx` — task detail/edit page  
3. Add tasks link to admin navigation
4. Use existing patterns from `/admin/shifts/page.tsx` for layout and API calls

## Dependencies
- Depends on: RAP-185 (tasks API)

## Risks
- Risk: No drag-and-drop library available → Mitigation: Use click-to-move buttons instead
