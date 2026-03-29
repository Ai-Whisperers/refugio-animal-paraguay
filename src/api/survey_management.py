"""Adopter satisfaction survey management API (RAP-264, EPIC-53).

Staff-only endpoints for survey dispatch tracking and result review.

Endpoints:
  GET  /api/admin/follow-up-surveys/stats       — aggregate survey completion stats
  GET  /api/admin/follow-up-surveys/pending     — follow-ups awaiting survey dispatch
  POST /api/admin/follow-up-surveys/mark-sent   — bulk mark surveys as sent
  GET  /api/admin/follow-up-surveys/results     — list completed survey responses
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.survey_management_service import (
    MarkSentResult,
    PendingSurvey,
    SurveyResult,
    SurveyStats,
    get_pending_surveys,
    get_survey_results,
    get_survey_stats,
    mark_surveys_sent,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/follow-up-surveys",
    tags=["follow-up-survey-management"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SurveyStatsResponse(BaseModel):
    total_scheduled: int
    total_sent: int
    total_completed: int
    send_rate_pct: float
    completion_rate_pct: float
    avg_welfare_score: float | None
    avg_satisfaction_score: float | None


class PendingSurveyResponse(BaseModel):
    follow_up_id: UUID
    adoption_request_id: UUID
    scheduled_date: datetime
    day_offset: int
    days_overdue: int


class MarkSentRequest(BaseModel):
    follow_up_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class MarkSentResponse(BaseModel):
    marked_count: int
    already_sent_count: int


class SurveyResultResponse(BaseModel):
    follow_up_id: UUID
    adoption_request_id: UUID
    day_offset: int
    welfare_score: int
    satisfaction_score: int
    survey_completed_at: datetime
    comments: str | None
    issues_noted: str | None


# ---------------------------------------------------------------------------
# Mappers
# ---------------------------------------------------------------------------


def _stats_to_response(stats: SurveyStats) -> SurveyStatsResponse:
    return SurveyStatsResponse(
        total_scheduled=stats.total_scheduled,
        total_sent=stats.total_sent,
        total_completed=stats.total_completed,
        send_rate_pct=stats.send_rate_pct,
        completion_rate_pct=stats.completion_rate_pct,
        avg_welfare_score=stats.avg_welfare_score,
        avg_satisfaction_score=stats.avg_satisfaction_score,
    )


def _pending_to_response(survey: PendingSurvey) -> PendingSurveyResponse:
    return PendingSurveyResponse(
        follow_up_id=survey.follow_up_id,
        adoption_request_id=survey.adoption_request_id,
        scheduled_date=survey.scheduled_date,
        day_offset=survey.day_offset,
        days_overdue=survey.days_overdue,
    )


def _result_to_response(result: SurveyResult) -> SurveyResultResponse:
    return SurveyResultResponse(
        follow_up_id=result.follow_up_id,
        adoption_request_id=result.adoption_request_id,
        day_offset=result.day_offset,
        welfare_score=result.welfare_score,
        satisfaction_score=result.satisfaction_score,
        survey_completed_at=result.survey_completed_at,
        comments=result.comments,
        issues_noted=result.issues_noted,
    )


def _mark_sent_to_response(result: MarkSentResult) -> MarkSentResponse:
    return MarkSentResponse(
        marked_count=result.marked_count,
        already_sent_count=result.already_sent_count,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/stats",
    response_model=SurveyStatsResponse,
    summary="Aggregate survey dispatch and satisfaction statistics",
)
async def survey_stats(
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> SurveyStatsResponse:
    """Return aggregate survey send rate, completion rate, and average scores.

    Auth: requires staff or admin role.
    """
    stats = await get_survey_stats(db)
    return _stats_to_response(stats)


@router.get(
    "/pending",
    response_model=list[PendingSurveyResponse],
    summary="List follow-ups awaiting survey dispatch",
)
async def pending_surveys(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[PendingSurveyResponse]:
    """Return follow-ups that are due but have not had their survey sent.

    Ordered by scheduled_date ascending (most overdue first).

    Auth: requires staff or admin role.
    """
    surveys = await get_pending_surveys(db, limit=limit, offset=offset)
    return [_pending_to_response(s) for s in surveys]


@router.post(
    "/mark-sent",
    response_model=MarkSentResponse,
    summary="Bulk mark surveys as sent",
)
async def mark_sent(
    payload: MarkSentRequest,
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> MarkSentResponse:
    """Mark a batch of follow-ups as having their survey dispatched.

    Sets survey_sent_at and transitions status to 'sent'.
    Idempotent — already-sent follow-ups are counted but not re-updated.

    Auth: requires staff or admin role.
    """
    result = await mark_surveys_sent(db, follow_up_ids=payload.follow_up_ids)
    return _mark_sent_to_response(result)


@router.get(
    "/results",
    response_model=list[SurveyResultResponse],
    summary="List completed survey responses",
)
async def survey_results(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    max_welfare_score: int | None = Query(
        default=None,
        ge=1,
        le=4,
        description="Filter to responses with welfare_score < this value (e.g. 3 = show scores 1-2)",
    ),
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[SurveyResultResponse]:
    """List completed adopter survey responses, newest first.

    Use max_welfare_score to surface low-welfare cases requiring attention.

    Auth: requires staff or admin role.
    """
    results = await get_survey_results(
        db,
        limit=limit,
        offset=offset,
        min_score=max_welfare_score,
    )
    return [_result_to_response(r) for r in results]
