"""API endpoints for adoption success scoring and analytics.

Provides staff/admin endpoints to view adoption scores, grade
distributions, analytics, and success stories.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_db
from src.services.adoption_success_service import (
    AdoptionNotFoundError,
    calculate_adoption_score,
    get_success_score_analytics,
    get_success_stories,
)

router = APIRouter(tags=["Adoption Success"])


# --- Schemas ---


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of score components."""

    followup_completion: int = 0
    no_issues: int = 0
    photo_submitted: int = 0
    no_return: int = 0
    trial_passed: int = 0

    model_config = {"from_attributes": True}


class AdoptionScoreResponse(BaseModel):
    """Score for a single adoption."""

    adoption_request_id: UUID
    score: int
    grade: str
    grade_color: str
    breakdown: ScoreBreakdown
    followups_completed: int
    followups_total: int
    has_return: bool

    model_config = {"from_attributes": True}


class GradeDistribution(BaseModel):
    """Count of adoptions per grade."""

    a_plus: int = 0
    a: int = 0
    b: int = 0
    c: int = 0

    model_config = {"from_attributes": True}


class SuccessAnalyticsResponse(BaseModel):
    """Aggregate success score analytics."""

    total_scored: int
    average_score: float
    grade_distribution: dict[str, int]

    model_config = {"from_attributes": True}


# --- Endpoints ---


@router.get(
    "/api/admin/adoptions/{adoption_request_id}/score",
    response_model=AdoptionScoreResponse,
)
async def get_adoption_score(
    adoption_request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Calculate and return the success score for an adoption."""
    try:
        return await calculate_adoption_score(db, adoption_request_id)
    except AdoptionNotFoundError:
        raise HTTPException(status_code=404, detail="Adoption request not found") from None


@router.get(
    "/api/admin/adoptions/analytics/success-scores",
    response_model=SuccessAnalyticsResponse,
)
async def get_success_analytics(
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Get aggregate success score metrics for all adoptions."""
    result = await get_success_score_analytics(db)
    # Remove individual scores from response (too large for aggregate endpoint)
    result.pop("scores", None)
    return result


@router.get(
    "/api/admin/adoptions/success-stories",
    response_model=list[AdoptionScoreResponse],
)
async def get_success_stories_endpoint(
    min_score: int = Query(default=90, ge=0, le=100),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> list[dict]:
    """Get high-scoring adoptions with photos (success stories)."""
    return await get_success_stories(db, min_score=min_score, limit=limit)
