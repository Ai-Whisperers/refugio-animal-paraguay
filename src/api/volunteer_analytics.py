"""Volunteer program analytics API (RAP-197).

Staff endpoint to view aggregate analytics for the volunteer program.

Endpoints:
    GET /api/staff/volunteers/analytics  -- program-wide analytics (staff only)
"""

import logging
from collections import Counter
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.volunteer_profile import VolunteerProfile, VolunteerStatus
from src.db.session import get_db

logger = logging.getLogger(__name__)

ANALYTICS_HISTORY_MONTHS = 6

router = APIRouter(prefix="/api/staff/volunteers", tags=["volunteer-analytics"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class SkillFrequency(BaseModel):
    """A single skill with its volunteer count."""

    skill: str
    count: int


class MonthlyCount(BaseModel):
    """Volunteer join count for a calendar month."""

    year: int
    month: int
    count: int


class VolunteerAnalyticsResponse(BaseModel):
    """Aggregate analytics for the volunteer program."""

    generated_at: date = Field(..., description="Date this report was generated")

    # Volume
    total_volunteers: int = Field(..., description="All volunteers regardless of status")
    total_approved: int = Field(..., description="Active approved volunteers")
    total_pending: int = Field(..., description="Pending applications")
    total_rejected: int = Field(..., description="Rejected applications")
    total_inactive: int = Field(..., description="Inactive volunteers")

    # Hours
    total_hours_logged: float = Field(
        ..., description="Sum of total_hours_logged across all approved volunteers"
    )
    avg_hours_per_volunteer: float = Field(
        ...,
        description="Average hours per approved volunteer (0.0 if none)",
    )

    # Distributions
    skills_distribution: list[SkillFrequency] = Field(
        default_factory=list,
        description="Skills sorted by frequency descending",
    )
    monthly_joins: list[MonthlyCount] = Field(
        default_factory=list,
        description=f"New volunteer profiles per month for the last {ANALYTICS_HISTORY_MONTHS} months",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _skills_distribution(profiles: list[VolunteerProfile]) -> list[SkillFrequency]:
    """Count skill occurrences across all profiles."""
    counter: Counter[str] = Counter()
    for profile in profiles:
        for skill in profile.skills or []:
            counter[skill] += 1
    return [SkillFrequency(skill=skill, count=count) for skill, count in counter.most_common()]


def _monthly_joins(profiles: list[VolunteerProfile], history_months: int) -> list[MonthlyCount]:
    """Count how many profiles were created each calendar month for the last N months."""
    today = datetime.now(UTC).date()
    # Build the list of (year, month) slots going back N months
    slots: list[tuple[int, int]] = []
    y, m = today.year, today.month
    for _ in range(history_months):
        slots.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    slots.reverse()  # chronological order

    counter: Counter[tuple[int, int]] = Counter()
    slot_set = set(slots)
    for profile in profiles:
        created = profile.created_at
        created_date = created.date() if hasattr(created, "date") else created  # type: ignore[assignment]
        key = (created_date.year, created_date.month)
        if key in slot_set:
            counter[key] += 1

    return [MonthlyCount(year=y, month=m, count=counter.get((y, m), 0)) for y, m in slots]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/analytics",
    response_model=VolunteerAnalyticsResponse,
    summary="Volunteer program analytics (staff only)",
)
async def get_volunteer_analytics(
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> Any:
    """Return aggregate analytics for the volunteer program.

    Computes statistics from volunteer_profiles including status breakdown,
    total hours, average hours, skill distribution, and monthly join trends.

    Staff only.
    """
    result = await db.execute(select(VolunteerProfile))
    all_profiles: list[VolunteerProfile] = list(result.scalars().all())

    approved = [p for p in all_profiles if p.status == VolunteerStatus.APPROVED]
    pending = [p for p in all_profiles if p.status == VolunteerStatus.PENDING]
    rejected = [p for p in all_profiles if p.status == VolunteerStatus.REJECTED]
    inactive = [p for p in all_profiles if p.status == VolunteerStatus.INACTIVE]

    total_hours = sum(float(p.total_hours_logged or 0) for p in approved)
    avg_hours = round(total_hours / len(approved), 2) if approved else 0.0

    logger.info(
        "Volunteer analytics requested: total=%d approved=%d total_hours=%.2f",
        len(all_profiles),
        len(approved),
        total_hours,
    )

    return VolunteerAnalyticsResponse(
        generated_at=datetime.now(UTC).date(),
        total_volunteers=len(all_profiles),
        total_approved=len(approved),
        total_pending=len(pending),
        total_rejected=len(rejected),
        total_inactive=len(inactive),
        total_hours_logged=round(total_hours, 2),
        avg_hours_per_volunteer=avg_hours,
        skills_distribution=_skills_distribution(all_profiles),
        monthly_joins=_monthly_joins(all_profiles, ANALYTICS_HISTORY_MONTHS),
    )
