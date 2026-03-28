# RAP-187 Plan

## Objective
Enhance the admin task board so staff can assign tasks to approved volunteers when creating or editing tasks.

## Description
The backend already accepts `assigned_to` (user UUID) on task create/update (RAP-185). This story adds the frontend UX: a volunteer picker in the Create Task modal, a reassign button on task cards, and display of the assignee name on each card.

## Acceptance Criteria
- [ ] Create Task modal includes a volunteer dropdown (approved volunteers only)
- [ ] Task card shows assigned volunteer name (or "Sin asignar")
- [ ] Reassign button on unfinished cards opens an assignment modal
- [ ] Empty state handled (no volunteers available)
- [ ] API errors surfaced to user

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [x] Solution affects ≤3 files
- [x] Change impact ≤10 lines of actual code — No, this is ~80 lines but in a single file
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Simple — single file change (tasks page) + volunteer fetch logic

## Approach
1. Add volunteer fetch (GET /api/volunteers?status=approved&page_size=100) to tasks page load
2. Extend CreateTaskModal with a `assigned_to` volunteer select
3. Add AssignModal for reassigning existing tasks
4. Show assignee name on TaskCard

## Dependencies
- Depends on: RAP-186 (tasks page exists), RAP-185 (backend supports assigned_to)

## Risks
- Volunteer list could be empty: handle gracefully with "Sin voluntarios disponibles"
