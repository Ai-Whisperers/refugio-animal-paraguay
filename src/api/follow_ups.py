"""Post-adoption follow-up router.

Endpoints:
  GET    /follow-ups                         - list follow-ups (filter by request/status)
  GET    /follow-ups/{id}                    - single follow-up detail
  POST   /follow-ups/schedule/{request_id}   - manually schedule follow-ups for a request
  POST   /follow-ups/{id}/survey             - submit welfare survey
  POST   /follow-ups/{id}/return             - record return/rehome
  GET    /follow-ups/analytics/outcomes       - adoption outcome statistics
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.follow_up import FollowUp
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.follow_up import (
    AdoptionOutcomeStats,
    FollowUpResponse,
    ReturnRecord,
    SurveySubmission,
)
from src.services.follow_up_service import (
    get_adoption_outcome_stats,
    get_follow_ups_for_request,
    record_return,
    schedule_follow_ups,
    submit_survey,
)

router = APIRouter(prefix="/follow-ups", tags=["follow-ups"], responses=RESOURCE_RESPONSES)

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


@router.get("/analytics/outcomes", response_model=AdoptionOutcomeStats)
async def adoption_outcomes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> dict:
    """Return aggregated adoption outcome statistics."""
    return await get_adoption_outcome_stats(db)


@router.get("", response_model=list[FollowUpResponse])
async def list_follow_ups(
    adoption_request_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[FollowUp]:
    """List follow-ups with optional filters."""
    stmt = select(FollowUp).offset(offset).limit(limit).order_by(FollowUp.scheduled_date)
    if adoption_request_id is not None:
        stmt = stmt.where(FollowUp.adoption_request_id == adoption_request_id)
    if status_filter is not None:
        stmt = stmt.where(FollowUp.status == status_filter)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{follow_up_id}", response_model=FollowUpResponse)
async def get_follow_up(
    follow_up_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> FollowUp:
    """Get a single follow-up by ID."""
    fu = await db.get(FollowUp, follow_up_id)
    if fu is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up not found",
        )
    return fu


@router.post(
    "/schedule/{request_id}",
    response_model=list[FollowUpResponse],
    status_code=status.HTTP_201_CREATED,
)
async def schedule_follow_ups_endpoint(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[FollowUp]:
    """Schedule follow-ups for an approved/completed adoption request."""
    req = await db.get(AdoptionRequest, request_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adoption request not found",
        )

    if req.status != AdoptionRequestStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Follow-ups can only be scheduled for approved requests",
        )

    completed_at = req.decided_at or datetime.now(UTC)
    follow_ups = await schedule_follow_ups(db, request_id, completed_at)

    if not follow_ups:
        # Already scheduled — return existing
        return await get_follow_ups_for_request(db, request_id)

    return follow_ups


@router.post(
    "/{follow_up_id}/survey",
    response_model=FollowUpResponse,
)
async def submit_follow_up_survey(
    follow_up_id: UUID,
    payload: SurveySubmission,
    db: AsyncSession = Depends(get_db),
) -> FollowUp:
    """Submit a welfare survey response for a follow-up."""
    try:
        return await submit_survey(
            db,
            follow_up_id,
            welfare_score=payload.welfare_score,
            satisfaction_score=payload.satisfaction_score,
            comments=payload.comments,
            photo_url=payload.photo_url,
            issues_noted=payload.issues_noted,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up not found",
        ) from None


@router.post(
    "/{follow_up_id}/return",
    response_model=FollowUpResponse,
)
async def record_follow_up_return(
    follow_up_id: UUID,
    payload: ReturnRecord,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> FollowUp:
    """Record a return/rehome event on a follow-up."""
    try:
        return await record_return(
            db,
            follow_up_id,
            return_reason_code=payload.return_reason_code.value,
            return_notes=payload.return_notes,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up not found",
        ) from None
