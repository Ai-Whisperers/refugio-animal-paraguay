"""API endpoints for adoption pipeline status tracking.

Provides staff/admin endpoints to advance adoption requests through
pipeline stages, reject applications, view transition history,
detect timeouts, and get pipeline summary stats.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.session import get_db
from src.services.pipeline_tracking_service import (
    AdoptionNotFoundError,
    AlreadyCompletedError,
    InvalidTransitionError,
    advance_adoption,
    get_adoption_with_stage,
    get_pipeline_summary,
    get_stage_history,
    get_timed_out_adoptions,
    reject_adoption,
)

router = APIRouter(tags=["Pipeline Tracking"])


# --- Schemas ---


class AdvanceRequest(BaseModel):
    """Request body for advancing an adoption through the pipeline."""

    notes: str | None = Field(None, max_length=2000)


class RejectRequest(BaseModel):
    """Request body for rejecting an adoption application."""

    reason: str = Field(..., min_length=1, max_length=2000)


class StageInfo(BaseModel):
    """Embedded stage details."""

    id: UUID
    name: str
    position: int
    color: str
    requires_approval: bool
    max_days: int | None = None

    model_config = {"from_attributes": True}


class AdoptionWithStageResponse(BaseModel):
    """Adoption request with current pipeline stage info."""

    id: UUID
    animal_id: UUID
    adopter_id: UUID
    status: str
    current_stage_id: UUID | None = None
    current_stage_started_at: datetime | None = None
    current_stage: StageInfo | None = None
    days_in_current_stage: int | None = None

    model_config = {"from_attributes": True}


class TransitionResponse(BaseModel):
    """Response after a stage transition."""

    adoption_request_id: UUID
    from_stage_id: UUID | None = None
    to_stage_id: UUID | None = None
    to_stage_name: str | None = None
    action: str
    notes: str | None = None
    reason: str | None = None
    transitioned_at: datetime

    model_config = {"from_attributes": True}


class StageLogEntry(BaseModel):
    """Single entry in the stage transition history."""

    id: UUID
    adoption_request_id: UUID
    from_stage_id: UUID | None = None
    to_stage_id: UUID | None = None
    action: str
    notes: str | None = None
    transitioned_by: UUID | None = None
    transitioned_at: datetime

    model_config = {"from_attributes": True}


class TimedOutAdoption(BaseModel):
    """An adoption that has exceeded its stage timeout."""

    adoption_request_id: UUID
    animal_id: UUID
    adopter_id: UUID
    stage_id: UUID
    stage_name: str
    max_days: int
    days_in_stage: int
    overdue_by: int

    model_config = {"from_attributes": True}


class PipelineStageSummary(BaseModel):
    """Count of adoptions in a pipeline stage."""

    stage_id: UUID
    stage_name: str
    position: int
    color: str
    adoption_count: int

    model_config = {"from_attributes": True}


# --- Endpoints ---


@router.get(
    "/api/admin/adoptions/{adoption_request_id}/pipeline",
    response_model=AdoptionWithStageResponse,
)
async def get_adoption_pipeline_status(
    adoption_request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Get an adoption request with its current pipeline stage details."""
    try:
        return await get_adoption_with_stage(db, adoption_request_id)
    except AdoptionNotFoundError:
        raise HTTPException(status_code=404, detail="Adoption request not found") from None


@router.post(
    "/api/admin/adoptions/{adoption_request_id}/advance",
    response_model=TransitionResponse,
)
async def advance_adoption_stage(
    adoption_request_id: UUID,
    body: AdvanceRequest,
    db: AsyncSession = Depends(get_db),
    staff: object = Depends(require_staff),
) -> dict:
    """Advance an adoption request to the next pipeline stage."""
    user_id = getattr(staff, "id", None)
    try:
        result = await advance_adoption(
            db,
            adoption_request_id,
            user_id=user_id,
            notes=body.notes,
        )
        await db.commit()
        return result
    except AdoptionNotFoundError:
        raise HTTPException(status_code=404, detail="Adoption request not found") from None
    except AlreadyCompletedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.post(
    "/api/admin/adoptions/{adoption_request_id}/reject",
    response_model=TransitionResponse,
)
async def reject_adoption_request(
    adoption_request_id: UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    admin: object = Depends(require_admin),
) -> dict:
    """Reject an adoption request at any stage. Admin only."""
    user_id = getattr(admin, "id", None)
    try:
        result = await reject_adoption(
            db,
            adoption_request_id,
            reason=body.reason,
            user_id=user_id,
        )
        await db.commit()
        return result
    except AdoptionNotFoundError:
        raise HTTPException(status_code=404, detail="Adoption request not found") from None
    except AlreadyCompletedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None


@router.get(
    "/api/admin/adoptions/{adoption_request_id}/history",
    response_model=list[StageLogEntry],
)
async def get_adoption_stage_history(
    adoption_request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> list[dict]:
    """Get the full stage transition history for an adoption request."""
    try:
        return await get_stage_history(db, adoption_request_id)
    except AdoptionNotFoundError:
        raise HTTPException(status_code=404, detail="Adoption request not found") from None


@router.get(
    "/api/admin/adoptions/timed-out",
    response_model=list[TimedOutAdoption],
)
async def get_timed_out_adoption_requests(
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> list[dict]:
    """Find adoption requests that have exceeded their stage's max_days timeout."""
    return await get_timed_out_adoptions(db)


@router.get(
    "/api/admin/adoptions/pipeline-summary",
    response_model=list[PipelineStageSummary],
)
async def get_adoption_pipeline_summary(
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> list[dict]:
    """Get count of active adoptions in each pipeline stage."""
    return await get_pipeline_summary(db)
