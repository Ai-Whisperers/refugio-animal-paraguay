# RAP-189 Plan

## Objective
Implement a GET /api/tasks/summary/daily endpoint that returns daily operational task counts grouped by status, category, and priority.

## Description
Staff need a dashboard-ready summary of task activity for a given day. The endpoint returns total, pending, in_progress, completed, cancelled, and overdue counts, a completion_rate, and breakdowns by category and priority. Defaults to today; accepts an explicit report_date query parameter.

## Acceptance Criteria
- [x] GET /api/tasks/summary/daily returns 200 with correct schema
- [x] Counts by status (pending, in_progress, completed, cancelled) are accurate
- [x] overdue counts non-terminal tasks where due_date < now
- [x] completion_rate = completed / (total - cancelled), 0.0 when no tasks
- [x] by_category and by_priority dicts aggregate correctly
- [x] report_date query param accepted (YYYY-MM-DD); defaults to today
- [x] Invalid date format returns 422
- [x] Empty state (no tasks) returns zeros throughout
- [x] 6 integration tests all pass

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — single file change (tasks.py), 1 new endpoint, 0 migrations, 0 frontend changes. Tests already committed to develop.

## Approach
1. Add `date, timedelta` to datetime imports
2. Add `DailyTaskSummary` Pydantic schema
3. Register `/api/tasks/summary/daily` on public_router BEFORE `/api/tasks/{task_id}` to prevent route shadowing
4. Compute counts with in-memory iteration over all tasks (acceptable volume for a shelter)

## Dependencies
- Depends on: RAP-185 (Task model) — already merged to develop
