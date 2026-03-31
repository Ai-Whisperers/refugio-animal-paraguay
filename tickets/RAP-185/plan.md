# RAP-185 Plan

## Objective
Implement a task model with categories and priorities for volunteer task assignment tracking in the shelter.

## Description
Create a SQLAlchemy ORM model for shelter tasks with categories (feeding, cleaning, walking, socialization, etc.), priorities (low/medium/high/urgent), statuses (pending/in_progress/completed/cancelled), and assignment to volunteers. Expose CRUD API endpoints for staff to manage tasks.

## Acceptance Criteria
- [ ] Task SQLAlchemy model with category, priority, status, assignee, due_date, notes
- [ ] Alembic migration 074 creating the tasks table
- [ ] FastAPI router with CRUD endpoints (staff-only create/update/delete, authenticated read)
- [ ] Pydantic v2 schemas for request/response validation
- [ ] OpenAPI docs for all endpoints
- [ ] Unit tests for schemas/enums (80%+ coverage)
- [ ] Integration tests for CRUD happy paths

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria
- [ ] Single, clear root cause identified — N/A (new feature)
- [x] Solution affects ≤3 files — NO: model + migration + API + tests + app.py
- [ ] Change impact ≤10 lines — NO: substantial new code

**Assessment result**: Complex — new model + migration + router + tests

## Approach
1. Create `src/db/models/task.py` with Task model (TaskStatus, TaskCategory, TaskPriority enums)
2. Create migration `074_create_tasks_table.py`
3. Create `src/api/tasks.py` with staff + public routers
4. Register routers in `src/app.py`
5. Write unit tests `tests/unit/test_tasks_schemas.py`
6. Write integration tests `tests/integration/test_tasks.py`

## Dependencies
- Depends on: shifts (RAP-180), volunteer profiles (RAP-176)

## Risks
- Risk: Task assignee may not be a registered volunteer → Mitigation: FK constraint + validation in API
