"""Pre-qualification analytics endpoints for the admin dashboard.

Endpoints:
    GET /admin/pre-qualification/analytics  -- aggregate stats
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.services.pre_qualification_analytics_service import get_analytics

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/pre-qualification",
    tags=["admin-pre-qualification-analytics"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas ---


class ScoreBucket(BaseModel):
    """Score distribution bucket."""

    bucket: str
    count: int


class FailureReasonStat(BaseModel):
    """A commonly failed requirement type with its count."""

    requirement_type: str
    count: int


class AnimalAttemptStat(BaseModel):
    """Per-animal attempt stats."""

    animal_id: UUID
    attempt_count: int
    qualified_count: int


class PreQualificationAnalyticsResponse(BaseModel):
    """Aggregate pre-qualification analytics."""

    total_attempts: int
    qualified_count: int
    disqualified_count: int
    qualification_rate: float
    average_score: float
    score_distribution: list[ScoreBucket]
    top_failure_reasons: list[FailureReasonStat]
    top_animals: list[AnimalAttemptStat]
    date_from: datetime | None = None
    date_to: datetime | None = None


# --- Endpoints ---


@router.get(
    "/analytics",
    response_model=PreQualificationAnalyticsResponse,
)
async def get_pre_qualification_analytics(
    date_from: datetime | None = Query(default=None, description="Start date filter"),
    date_to: datetime | None = Query(default=None, description="End date filter"),
    animal_id: UUID | None = Query(default=None, description="Filter by animal"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> PreQualificationAnalyticsResponse:
    """Get aggregate pre-qualification analytics for the admin dashboard.

    Returns pass/fail rates, score distributions, common failure reasons,
    and per-animal breakdown. Optionally filtered by date range or animal.
    """
    result = await get_analytics(
        db=db,
        date_from=date_from,
        date_to=date_to,
        animal_id=animal_id,
    )

    return PreQualificationAnalyticsResponse(
        total_attempts=result["total_attempts"],
        qualified_count=result["qualified_count"],
        disqualified_count=result["disqualified_count"],
        qualification_rate=result["qualification_rate"],
        average_score=result["average_score"],
        score_distribution=[
            ScoreBucket(bucket=b["bucket"], count=b["count"]) for b in result["score_distribution"]
        ],
        top_failure_reasons=[
            FailureReasonStat(requirement_type=f["requirement_type"], count=f["count"])
            for f in result["top_failure_reasons"]
        ],
        top_animals=[
            AnimalAttemptStat(
                animal_id=UUID(a["animal_id"]),
                attempt_count=a["attempt_count"],
                qualified_count=a["qualified_count"],
            )
            for a in result["top_animals"]
        ],
        date_from=datetime.fromisoformat(result["date_from"]) if result["date_from"] else None,
        date_to=datetime.fromisoformat(result["date_to"]) if result["date_to"] else None,
    )
