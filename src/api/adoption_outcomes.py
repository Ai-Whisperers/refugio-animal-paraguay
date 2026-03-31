"""Adoption outcome tracking API endpoints (RAP-260, EPIC-53).

Staff-only endpoints for recording and querying the high-level outcome
of completed adoptions.

Endpoints:
  POST   /api/admin/adoptions/{adoption_request_id}/outcome  — record outcome
  GET    /api/admin/adoptions/{adoption_request_id}/outcome  — get outcome
  PUT    /api/admin/adoptions/{adoption_request_id}/outcome  — update outcome
  GET    /api/admin/adoption-outcomes                        — list all outcomes
  GET    /api/admin/adoption-outcomes/stats                  — aggregate statistics
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.adoption_outcome import AdoptionOutcomeType
from src.db.models.user import User
from src.db.session import get_db
from src.services.adoption_outcome_service import (
    AdoptionOutcomeNotFoundError,
    DuplicateAdoptionOutcomeError,
    OutcomeRecord,
    OutcomeStats,
    create_outcome,
    get_outcome_by_adoption,
    get_outcome_stats,
    list_outcomes,
    update_outcome,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin",
    tags=["adoption-outcomes"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 200

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CreateOutcomeRequest(BaseModel):
    outcome_type: AdoptionOutcomeType
    outcome_date: datetime | None = None
    notes: str | None = None
    return_reason_code: str | None = None
    return_date: datetime | None = None


class UpdateOutcomeRequest(BaseModel):
    outcome_type: AdoptionOutcomeType | None = None
    outcome_date: datetime | None = None
    notes: str | None = None
    return_reason_code: str | None = None
    return_date: datetime | None = None
    refresh_scores: bool = True


class OutcomeResponse(BaseModel):
    id: UUID
    adoption_request_id: UUID
    outcome_type: str
    outcome_date: datetime | None
    notes: str | None
    avg_welfare_score: float | None
    avg_satisfaction_score: float | None
    total_follow_ups: int
    completed_follow_ups: int
    return_reason_code: str | None
    return_date: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OutcomeStatsResponse(BaseModel):
    total_outcomes: int
    successful: int
    returned: int
    rehomed: int
    deceased: int
    unknown: int
    success_rate_pct: float
    return_rate_pct: float
    avg_welfare_score: float | None
    avg_satisfaction_score: float | None
    avg_followup_completion_rate_pct: float
    generated_at: str


def _outcome_to_response(record: OutcomeRecord) -> OutcomeResponse:
    return OutcomeResponse(
        id=record.id,
        adoption_request_id=record.adoption_request_id,
        outcome_type=record.outcome_type,
        outcome_date=record.outcome_date,
        notes=record.notes,
        avg_welfare_score=record.avg_welfare_score,
        avg_satisfaction_score=record.avg_satisfaction_score,
        total_follow_ups=record.total_follow_ups,
        completed_follow_ups=record.completed_follow_ups,
        return_reason_code=record.return_reason_code,
        return_date=record.return_date,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _stats_to_response(stats: OutcomeStats) -> OutcomeStatsResponse:
    return OutcomeStatsResponse(
        total_outcomes=stats.total_outcomes,
        successful=stats.successful,
        returned=stats.returned,
        rehomed=stats.rehomed,
        deceased=stats.deceased,
        unknown=stats.unknown,
        success_rate_pct=stats.success_rate_pct,
        return_rate_pct=stats.return_rate_pct,
        avg_welfare_score=stats.avg_welfare_score,
        avg_satisfaction_score=stats.avg_satisfaction_score,
        avg_followup_completion_rate_pct=stats.avg_followup_completion_rate_pct,
        generated_at=stats.generated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/adoptions/{adoption_request_id}/outcome",
    response_model=OutcomeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record outcome for an adoption",
)
async def create_adoption_outcome(
    adoption_request_id: UUID,
    body: CreateOutcomeRequest,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> OutcomeResponse:
    """Record the final outcome for a completed adoption.

    Creates a single outcome record per adoption. Follow-up scores are
    automatically aggregated from existing FollowUp rows.

    Auth: requires staff or admin role.
    """
    try:
        record = await create_outcome(
            db,
            adoption_request_id=adoption_request_id,
            outcome_type=body.outcome_type,
            outcome_date=body.outcome_date,
            notes=body.notes,
            return_reason_code=body.return_reason_code,
            return_date=body.return_date,
        )
    except DuplicateAdoptionOutcomeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Outcome already exists for adoption {adoption_request_id}",
        ) from exc
    return _outcome_to_response(record)


@router.get(
    "/adoptions/{adoption_request_id}/outcome",
    response_model=OutcomeResponse,
    summary="Get outcome for an adoption",
)
async def get_adoption_outcome(
    adoption_request_id: UUID,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> OutcomeResponse:
    """Retrieve the outcome record for a specific adoption.

    Auth: requires staff or admin role.
    """
    try:
        record = await get_outcome_by_adoption(db, adoption_request_id)
    except AdoptionOutcomeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No outcome found for adoption {adoption_request_id}",
        ) from exc
    return _outcome_to_response(record)


@router.put(
    "/adoptions/{adoption_request_id}/outcome",
    response_model=OutcomeResponse,
    summary="Update outcome for an adoption",
)
async def update_adoption_outcome(
    adoption_request_id: UUID,
    body: UpdateOutcomeRequest,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> OutcomeResponse:
    """Update an existing adoption outcome record.

    Only the fields provided in the request body are changed. Set
    refresh_scores=true (default) to recalculate follow-up aggregates.

    Auth: requires staff or admin role.
    """
    try:
        record = await update_outcome(
            db,
            adoption_request_id=adoption_request_id,
            outcome_type=body.outcome_type,
            outcome_date=body.outcome_date,
            notes=body.notes,
            return_reason_code=body.return_reason_code,
            return_date=body.return_date,
            refresh_scores=body.refresh_scores,
        )
    except AdoptionOutcomeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No outcome found for adoption {adoption_request_id}",
        ) from exc
    return _outcome_to_response(record)


@router.get(
    "/adoption-outcomes",
    response_model=list[OutcomeResponse],
    summary="List all adoption outcomes",
)
async def list_adoption_outcomes(
    outcome_type: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_LIST_LIMIT, ge=1, le=MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0),
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[OutcomeResponse]:
    """List adoption outcome records with optional filtering.

    Auth: requires staff or admin role.
    """
    records = await list_outcomes(db, outcome_type=outcome_type, limit=limit, offset=offset)
    return [_outcome_to_response(r) for r in records]


@router.get(
    "/adoption-outcomes/stats",
    response_model=OutcomeStatsResponse,
    summary="Aggregate adoption outcome statistics",
)
async def adoption_outcome_stats(
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> OutcomeStatsResponse:
    """Return aggregate statistics: success rate, return rate, satisfaction scores.

    Auth: requires staff or admin role.
    """
    stats = await get_outcome_stats(db)
    return _stats_to_response(stats)
