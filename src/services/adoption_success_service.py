"""Service layer for adoption success scoring.

Calculates a 0-100 success score per adoption based on follow-up
completion, issues, photos, and return status. Provides grading,
analytics, and trend analysis.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.follow_up import FollowUp, FollowUpStatus

logger = logging.getLogger(__name__)

# Scoring weights (configurable)
POINTS_FOLLOWUP_COMPLETED = 20
POINTS_NO_ISSUES = 10
POINTS_PHOTO_SUBMITTED = 5
POINTS_NO_RETURN = 30
POINTS_TRIAL_PASSED = 20
MAX_SCORE = 100

# Grade thresholds
GRADE_A_PLUS_MIN = 90
GRADE_A_MIN = 80
GRADE_B_MIN = 70


class AdoptionScoringError(Exception):
    """Base error for scoring operations."""


class AdoptionNotFoundError(AdoptionScoringError):
    """Raised when the adoption request does not exist."""


def calculate_grade(score: int) -> str:
    """Convert a numeric score (0-100) to a letter grade."""
    if score >= GRADE_A_PLUS_MIN:
        return "A+"
    if score >= GRADE_A_MIN:
        return "A"
    if score >= GRADE_B_MIN:
        return "B"
    return "C"


def grade_color(grade: str) -> str:
    """Return a hex color for a grade."""
    colors = {
        "A+": "#22C55E",
        "A": "#3B82F6",
        "B": "#EAB308",
        "C": "#EF4444",
    }
    return colors.get(grade, "#6B7280")


async def calculate_adoption_score(
    db: AsyncSession,
    adoption_request_id: UUID,
) -> dict:
    """Calculate the success score for a single adoption.

    Score is based on:
    - Follow-up completion: +20 per completed (max capped at MAX_SCORE)
    - No issues reported across all follow-ups: +10
    - At least one photo submitted: +5
    - No return request filed: +30
    - Trial period passed (>90 days since adoption): +20
    """
    from src.db.models.adoption_request import AdoptionRequest
    from src.db.models.return_request import ReturnRequest

    # Verify adoption exists
    adoption_result = await db.execute(
        select(AdoptionRequest).where(AdoptionRequest.id == adoption_request_id)
    )
    adoption = adoption_result.scalar_one_or_none()
    if adoption is None:
        raise AdoptionNotFoundError(f"Adoption {adoption_request_id} not found")

    # Get follow-ups for this adoption
    fu_result = await db.execute(
        select(FollowUp).where(FollowUp.adoption_request_id == adoption_request_id)
    )
    follow_ups = list(fu_result.scalars().all())

    score = 0
    breakdown = {}

    # Follow-up completion points
    completed_count = sum(1 for fu in follow_ups if fu.status == FollowUpStatus.COMPLETED.value)
    total_followups = len(follow_ups)
    followup_points = min(completed_count * POINTS_FOLLOWUP_COMPLETED, MAX_SCORE)
    score += followup_points
    breakdown["followup_completion"] = followup_points

    # No issues reported
    has_issues = any(fu.issues_noted for fu in follow_ups)
    no_issues_points = POINTS_NO_ISSUES if not has_issues else 0
    score += no_issues_points
    breakdown["no_issues"] = no_issues_points

    # Photo submitted
    has_photos = any(fu.photo_url for fu in follow_ups)
    photo_points = POINTS_PHOTO_SUBMITTED if has_photos else 0
    score += photo_points
    breakdown["photo_submitted"] = photo_points

    # No return request
    return_count_result = await db.execute(
        select(func.count())
        .select_from(ReturnRequest)
        .where(ReturnRequest.adoption_request_id == adoption_request_id)
    )
    has_return = return_count_result.scalar_one() > 0
    no_return_points = POINTS_NO_RETURN if not has_return else 0
    score += no_return_points
    breakdown["no_return"] = no_return_points

    # Trial period passed (>90 days since adoption decision)
    trial_points = 0
    if adoption.decided_at:
        days_since = (datetime.now(UTC) - adoption.decided_at).days
        if days_since > 90:
            trial_points = POINTS_TRIAL_PASSED
    score += trial_points
    breakdown["trial_passed"] = trial_points

    # Cap at MAX_SCORE
    final_score = min(score, MAX_SCORE)
    grade = calculate_grade(final_score)

    return {
        "adoption_request_id": adoption_request_id,
        "score": final_score,
        "grade": grade,
        "grade_color": grade_color(grade),
        "breakdown": breakdown,
        "followups_completed": completed_count,
        "followups_total": total_followups,
        "has_return": has_return,
    }


async def get_success_score_analytics(
    db: AsyncSession,
) -> dict:
    """Calculate aggregate success score metrics.

    Returns average score, grade distribution, and summary stats.
    Scores are calculated on-the-fly from follow-up data.
    """

    # Get all approved/completed adoptions that have follow-ups
    adoptions_with_followups = await db.execute(select(func.distinct(FollowUp.adoption_request_id)))
    adoption_ids = [row[0] for row in adoptions_with_followups]

    if not adoption_ids:
        return {
            "total_scored": 0,
            "average_score": 0.0,
            "grade_distribution": {"A+": 0, "A": 0, "B": 0, "C": 0},
            "scores": [],
        }

    # Calculate scores for each adoption
    scores = []
    for adoption_id in adoption_ids:
        try:
            score_data = await calculate_adoption_score(db, adoption_id)
            scores.append(score_data)
        except AdoptionNotFoundError:
            continue

    if not scores:
        return {
            "total_scored": 0,
            "average_score": 0.0,
            "grade_distribution": {"A+": 0, "A": 0, "B": 0, "C": 0},
            "scores": [],
        }

    total_scored = len(scores)
    avg_score = round(sum(s["score"] for s in scores) / total_scored, 1)

    # Grade distribution
    grade_dist = {"A+": 0, "A": 0, "B": 0, "C": 0}
    for s in scores:
        grade_dist[s["grade"]] += 1

    return {
        "total_scored": total_scored,
        "average_score": avg_score,
        "grade_distribution": grade_dist,
        "scores": scores,
    }


async def get_success_stories(
    db: AsyncSession,
    min_score: int = GRADE_A_PLUS_MIN,
    limit: int = 10,
) -> list[dict]:
    """Find high-scoring adoptions that have photos (success stories).

    Returns adoptions with score >= min_score and at least one photo.
    """
    # Get adoptions with photos in their follow-ups
    photo_adoptions = await db.execute(
        select(func.distinct(FollowUp.adoption_request_id)).where(FollowUp.photo_url.isnot(None))
    )
    adoption_ids = [row[0] for row in photo_adoptions]

    stories = []
    for adoption_id in adoption_ids:
        try:
            score_data = await calculate_adoption_score(db, adoption_id)
            if score_data["score"] >= min_score:
                stories.append(score_data)
        except AdoptionNotFoundError:
            continue

    # Sort by score descending, limit
    stories.sort(key=lambda s: s["score"], reverse=True)
    return stories[:limit]
