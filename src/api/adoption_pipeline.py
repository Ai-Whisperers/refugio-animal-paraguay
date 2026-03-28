"""Adoption pipeline stage management API endpoints.

Staff can configure the adoption pipeline by creating, updating,
reordering, and toggling stages.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_async_session
from src.services.adoption_pipeline_service import (
    DuplicateStageError,
    MaxStagesError,
    PipelineError,
    StageNotFoundError,
    create_stage,
    delete_stage,
    get_stage,
    list_stages,
    reorder_stages,
    toggle_stage,
    update_stage,
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class StageCreateRequest(BaseModel):
    """Request body for creating a pipeline stage."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    requires_approval: bool = True
    max_days: int | None = Field(None, gt=0)
    color: str = "#6B7280"


class StageUpdateRequest(BaseModel):
    """Request body for updating a pipeline stage."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    requires_approval: bool | None = None
    max_days: int | None = Field(None, gt=0)
    color: str | None = None


class StageToggleRequest(BaseModel):
    """Request body for toggling a stage."""

    is_active: bool


class StageReorderRequest(BaseModel):
    """Request body for reordering stages."""

    stage_ids: list[UUID]


class StageResponse(BaseModel):
    """Pipeline stage response."""

    id: UUID
    name: str
    description: str | None = None
    position: int
    is_active: bool
    requires_approval: bool
    max_days: int | None = None
    color: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise_stage(stage: object) -> dict:
    """Convert a pipeline stage ORM object to a response dict."""
    return {
        "id": stage.id,  # type: ignore[attr-defined]
        "name": stage.name,  # type: ignore[attr-defined]
        "description": stage.description,  # type: ignore[attr-defined]
        "position": stage.position,  # type: ignore[attr-defined]
        "is_active": stage.is_active,  # type: ignore[attr-defined]
        "requires_approval": stage.requires_approval,  # type: ignore[attr-defined]
        "max_days": stage.max_days,  # type: ignore[attr-defined]
        "color": stage.color,  # type: ignore[attr-defined]
        "created_at": stage.created_at.isoformat(),  # type: ignore[attr-defined]
        "updated_at": stage.updated_at.isoformat(),  # type: ignore[attr-defined]
    }


def _handle_pipeline_error(exc: Exception) -> None:
    """Map service-layer exceptions to HTTP responses."""
    if isinstance(exc, StageNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, DuplicateStageError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, MaxStagesError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, PipelineError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/admin/adoption-pipeline",
    tags=["adoption-pipeline"],
    dependencies=[Depends(require_staff)],
)


@router.post(
    "/stages",
    response_model=StageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pipeline_stage(
    body: StageCreateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Create a new pipeline stage at the end of the pipeline."""
    try:
        stage = await create_stage(
            name=body.name,
            description=body.description,
            requires_approval=body.requires_approval,
            max_days=body.max_days,
            color=body.color,
            db=db,
        )
        await db.commit()
        return _serialise_stage(stage)
    except Exception as exc:
        _handle_pipeline_error(exc)
        raise


@router.get("/stages", response_model=list[StageResponse])
async def list_pipeline_stages(
    active_only: bool = False,
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """List all pipeline stages ordered by position."""
    stages = await list_stages(db, active_only=active_only)
    return [_serialise_stage(s) for s in stages]


@router.get("/stages/{stage_id}", response_model=StageResponse)
async def get_pipeline_stage(
    stage_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get a pipeline stage by ID."""
    try:
        stage = await get_stage(stage_id, db)
        return _serialise_stage(stage)
    except Exception as exc:
        _handle_pipeline_error(exc)
        raise


@router.patch("/stages/{stage_id}", response_model=StageResponse)
async def update_pipeline_stage(
    stage_id: UUID,
    body: StageUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Update a pipeline stage."""
    try:
        stage = await update_stage(
            stage_id=stage_id,
            name=body.name,
            description=body.description,
            requires_approval=body.requires_approval,
            max_days=body.max_days,
            color=body.color,
            db=db,
        )
        await db.commit()
        return _serialise_stage(stage)
    except Exception as exc:
        _handle_pipeline_error(exc)
        raise


@router.patch(
    "/stages/{stage_id}/toggle",
    response_model=StageResponse,
)
async def toggle_pipeline_stage(
    stage_id: UUID,
    body: StageToggleRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Activate or deactivate a pipeline stage."""
    try:
        stage = await toggle_stage(
            stage_id=stage_id,
            is_active=body.is_active,
            db=db,
        )
        await db.commit()
        return _serialise_stage(stage)
    except Exception as exc:
        _handle_pipeline_error(exc)
        raise


@router.put("/stages/reorder", response_model=list[StageResponse])
async def reorder_pipeline_stages(
    body: StageReorderRequest,
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Reorder pipeline stages by providing the desired order."""
    try:
        stages = await reorder_stages(
            stage_ids=body.stage_ids,
            db=db,
        )
        await db.commit()
        return [_serialise_stage(s) for s in stages]
    except Exception as exc:
        _handle_pipeline_error(exc)
        raise


@router.delete(
    "/stages/{stage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pipeline_stage(
    stage_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete a pipeline stage and reorder remaining stages."""
    try:
        await delete_stage(stage_id=stage_id, db=db)
        await db.commit()
    except Exception as exc:
        _handle_pipeline_error(exc)
        raise
