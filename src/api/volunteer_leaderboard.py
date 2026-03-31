"""Volunteer leaderboard and recognition API (RAP-196).

Staff endpoint to view top volunteers ranked by total hours logged.

Endpoints:
    GET /api/staff/volunteers/leaderboard  -- ranked list of volunteers by hours (staff only)
"""

import logging
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.models.volunteer_profile import VolunteerProfile, VolunteerStatus
from src.db.session import get_db

logger = logging.getLogger(__name__)

LEADERBOARD_DEFAULT_LIMIT = 10
LEADERBOARD_MAX_LIMIT = 50

router = APIRouter(prefix="/api/staff/volunteers", tags=["volunteer-leaderboard"])


# ---------------------------------------------------------------------------
# Period helpers
# ---------------------------------------------------------------------------

VALID_PERIODS = frozenset({"all", "month", "quarter", "year"})


def _period_start_date(period: str) -> date | None:
    """Return the start date for the given period, or None for 'all'."""
    today = datetime.now(UTC).date()
    if period == "month":
        return today.replace(day=1)
    if period == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return today.replace(month=quarter_start_month, day=1)
    if period == "year":
        return today.replace(month=1, day=1)
    return None  # "all"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LeaderboardEntry(BaseModel):
    """A single volunteer entry on the leaderboard."""

    rank: int = Field(..., description="1-based rank position")
    volunteer_id: UUID = Field(..., description="Volunteer profile ID")
    user_id: UUID = Field(..., description="User account ID")
    full_name: str | None = Field(None, description="Volunteer's full name")
    email: str = Field(..., description="Volunteer's email")
    total_hours_logged: float = Field(..., description="Total hours logged (all time)")
    skills: list[str] = Field(default_factory=list, description="Volunteer skill tags")

    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    """Leaderboard response — top volunteers ranked by total hours."""

    period: str = Field(..., description="Time period filter: all, month, quarter, year")
    period_start: date | None = Field(None, description="Start date of the period (null for 'all')")
    entries: list[LeaderboardEntry]
    total_approved_volunteers: int = Field(
        ..., description="Total number of approved volunteers in the system"
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Volunteer leaderboard ranked by hours (staff only)",
)
async def get_volunteer_leaderboard(
    limit: int = Query(
        LEADERBOARD_DEFAULT_LIMIT,
        ge=1,
        le=LEADERBOARD_MAX_LIMIT,
        description="Number of top volunteers to return (max 50)",
    ),
    period: str = Query(
        "all",
        description="Time period: all, month, quarter, year",
    ),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> Any:
    """Return the top N approved volunteers ranked by total hours logged.

    The `period` parameter currently uses the `total_hours_logged` snapshot
    stored on the volunteer profile (all-time value). Period filtering will
    be enhanced in a future story once per-entry date data is aggregated.

    Staff only.
    """
    if period not in VALID_PERIODS:
        period = "all"

    period_start = _period_start_date(period)

    # Count total approved volunteers
    count_result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.status == VolunteerStatus.APPROVED)
    )
    approved_profiles = count_result.scalars().all()
    total_approved = len(approved_profiles)

    # Sort by total_hours_logged descending, take top N
    sorted_profiles = sorted(
        approved_profiles,
        key=lambda p: float(p.total_hours_logged or 0),
        reverse=True,
    )[:limit]

    if not sorted_profiles:
        return LeaderboardResponse(
            period=period,
            period_start=period_start,
            entries=[],
            total_approved_volunteers=total_approved,
        )

    # Fetch user details for the top volunteers
    user_ids = [p.user_id for p in sorted_profiles]
    users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_by_id: dict[UUID, User] = {u.id: u for u in users_result.scalars().all()}

    entries = []
    for rank, profile in enumerate(sorted_profiles, start=1):
        user = users_by_id.get(profile.user_id)
        if user is None:
            continue
        entries.append(
            LeaderboardEntry(
                rank=rank,
                volunteer_id=profile.id,
                user_id=profile.user_id,
                full_name=user.full_name,
                email=user.email,
                total_hours_logged=round(float(profile.total_hours_logged or 0), 2),
                skills=list(profile.skills or []),
            )
        )

    logger.info(
        "Volunteer leaderboard requested: period=%s, limit=%d, results=%d",
        period,
        limit,
        len(entries),
    )

    return LeaderboardResponse(
        period=period,
        period_start=period_start,
        entries=entries,
        total_approved_volunteers=total_approved,
    )
