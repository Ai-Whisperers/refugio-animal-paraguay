"""Volunteer task assignment and tracking API (RAP-185).

Staff can create, update, and delete tasks. All authenticated users can view tasks.
Tasks can be assigned to volunteers, linked to animals, and tracked through completion.

Endpoints:
    POST   /api/tasks                    -- create task (staff only)
    GET    /api/tasks                    -- list tasks (authenticated)
    GET    /api/tasks/{id}               -- get task detail (authenticated)
    PATCH  /api/tasks/{id}               -- update task (staff only)
    DELETE /api/tasks/{id}               -- delete task (staff only)
    GET    /api/tasks/categories         -- list valid categories
    GET    /api/tasks/priorities         -- list valid priorities
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user as get_current_user
from src.auth.dependencies import require_staff
from src.db.models.task import (
    VALID_TASK_CATEGORIES,
    VALID_TASK_STATUSES,
    Task,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)
from src.db.models.user import User
from src.db.session import get_db

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

staff_router = APIRouter(tags=["Tasks"])
public_router = APIRouter(tags=["Tasks"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TaskCreateRequest(BaseModel):
    """Payload for creating a new task."""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Short descriptive task title"
    )
    description: str | None = Field(None, description="Detailed task description")
    category: TaskCategory = Field(default=TaskCategory.OTHER, description="Task category")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    assigned_to: UUID | None = Field(None, description="User ID of assigned volunteer")
    due_date: datetime | None = Field(None, description="When the task must be completed")
    animal_id: UUID | None = Field(None, description="Animal this task is related to")


class TaskUpdateRequest(BaseModel):
    """Payload for updating an existing task."""

    title: str | None = Field(None, max_length=200)
    description: str | None = None
    category: TaskCategory | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    assigned_to: UUID | None = None
    due_date: datetime | None = None
    animal_id: UUID | None = None
    completion_notes: str | None = Field(None, max_length=2000)


class TaskResponse(BaseModel):
    """Task detail response."""

    id: UUID
    created_by: UUID
    assigned_to: UUID | None
    title: str
    description: str | None
    category: str
    priority: str
    status: str
    due_date: datetime | None
    completed_at: datetime | None
    completion_notes: str | None
    animal_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskCategoriesResponse(BaseModel):
    """Available task category options."""

    categories: list[str]


class TaskPrioritiesResponse(BaseModel):
    """Available task priority options."""

    priorities: list[str]


# ---------------------------------------------------------------------------
# Endpoints — Public (read-only, authenticated)
# ---------------------------------------------------------------------------


@public_router.get("/api/tasks/categories", response_model=TaskCategoriesResponse)
async def list_task_categories() -> TaskCategoriesResponse:
    """Return all valid task category values."""
    return TaskCategoriesResponse(categories=sorted(VALID_TASK_CATEGORIES))


@public_router.get("/api/tasks/priorities", response_model=TaskPrioritiesResponse)
async def list_task_priorities() -> TaskPrioritiesResponse:
    """Return all valid task priority values."""
    priority_order = ["urgent", "high", "medium", "low"]
    return TaskPrioritiesResponse(priorities=priority_order)


@public_router.get("/api/tasks", response_model=TaskListResponse)
async def list_tasks(
    task_status: str | None = Query(None, description="Filter by status"),
    category: TaskCategory | None = Query(None, description="Filter by category"),
    priority: TaskPriority | None = Query(None, description="Filter by priority"),
    assigned_to: UUID | None = Query(None, description="Filter by assigned volunteer ID"),
    animal_id: UUID | None = Query(None, description="Filter by animal ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> TaskListResponse:
    """List tasks with optional filters. Requires authentication."""
    if task_status and task_status not in VALID_TASK_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Must be one of: {sorted(VALID_TASK_STATUSES)}",
        )

    filters = []
    if task_status:
        filters.append(Task.status == task_status)
    if category:
        filters.append(Task.category == category.value)
    if priority:
        filters.append(Task.priority == priority.value)
    if assigned_to:
        filters.append(Task.assigned_to == assigned_to)
    if animal_id:
        filters.append(Task.animal_id == animal_id)

    count_stmt = select(func.count()).select_from(Task)
    if filters:
        count_stmt = count_stmt.where(and_(*filters))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    stmt = select(Task).order_by(
        Task.priority.desc(),
        Task.due_date.asc().nullslast(),
        Task.created_at.desc(),
    )
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@public_router.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> TaskResponse:
    """Get a single task by ID. Requires authentication."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return TaskResponse.model_validate(task)


# ---------------------------------------------------------------------------
# Endpoints — Staff only (write operations)
# ---------------------------------------------------------------------------


@staff_router.post("/api/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> TaskResponse:
    """Create a new task. Staff only."""
    task = Task(
        created_by=current_user.id,
        assigned_to=body.assigned_to,
        title=body.title,
        description=body.description,
        category=body.category.value,
        priority=body.priority.value,
        status=TaskStatus.PENDING.value,
        due_date=body.due_date,
        animal_id=body.animal_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    logger.info(
        "Task created",
        extra={"task_id": str(task.id), "staff_id": str(current_user.id)},
    )
    return TaskResponse.model_validate(task)


@staff_router.patch("/api/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    body: TaskUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> TaskResponse:
    """Update a task. Staff only."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.category is not None:
        task.category = body.category.value
    if body.priority is not None:
        task.priority = body.priority.value
    if body.assigned_to is not None:
        task.assigned_to = body.assigned_to
    if body.due_date is not None:
        task.due_date = body.due_date
    if body.animal_id is not None:
        task.animal_id = body.animal_id
    if body.completion_notes is not None:
        task.completion_notes = body.completion_notes

    if body.status is not None:
        task.status = body.status.value
        # Auto-set completed_at when marking as completed
        if body.status == TaskStatus.COMPLETED and task.completed_at is None:
            task.completed_at = datetime.now(UTC)
        elif body.status != TaskStatus.COMPLETED:
            task.completed_at = None

    await db.commit()
    await db.refresh(task)
    logger.info(
        "Task updated",
        extra={"task_id": str(task_id), "staff_id": str(current_user.id)},
    )
    return TaskResponse.model_validate(task)


@staff_router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    """Delete a task. Staff only."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    await db.delete(task)
    await db.commit()
    logger.info(
        "Task deleted",
        extra={"task_id": str(task_id), "staff_id": str(current_user.id)},
    )
