"""Volunteer impact metrics API (RAP-199).

Staff endpoint to view shelter-wide impact metrics driven by volunteer activity:
hours contributed, activity breakdown by category, and top contributors.

Endpoints:
    GET /api/staff/volunteers/impact  -- program-wide impact metrics (staff only)
"""

import logging
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.volunteer_hours import HoursCategory, VolunteerHoursLog
from src.db.models.volunteer_profile import VolunteerProfile, VolunteerStatus
from src.db.session import get_db

logger = logging.getLogger(__name__)

IMPACT_DEFAULT_WINDOW_DAYS = 30
IMPACT_MAX_WINDOW_DAYS = 365

router = APIRouter(prefix="/api/staff/volunteers", tags=["volunteer-impact"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CategoryBreakdown(BaseModel):
    """Hours logged per category (approved entries only)."""

    category: str
    label: str
    hours: float


class TopContributor(BaseModel):
    """A volunteer in the top contributors list."""

    volunteer_id: str
    total_hours_logged: float


class ImpactMetricsResponse(BaseModel):
    """Shelter-wide volunteer impact metrics."""

    generated_at: date = Field(..., description="Date this report was generated")

    # Volunteer headcounts
    total_approved_volunteers: int
    total_volunteers_with_hours: int = Field(
        ..., description="Approved volunteers who have at least one hour logged"
    )

    # Hours from denormalised profile totals (all-time)
    total_hours_contributed: float = Field(
        ...,
        description="Sum of total_hours_logged across all approved volunteer profiles (all-time)",
    )

    # Hours from the hours log table (filterable by window)
    window_days: int = Field(..., description="Time window in days for log-based metrics")
    window_start: date = Field(..., description="Start date of the log window")
    hours_logged_in_window: float = Field(
        ...,
        description="Sum of approved hours from volunteer_hours_log within the window",
    )
    hours_pending_approval: float = Field(
        ...,
        description="Sum of unapproved hours in volunteer_hours_log within the window",
    )

    # Category breakdown for approved hours in window
    hours_by_category: list[CategoryBreakdown] = Field(
        default_factory=list,
        description="Approved hours broken down by activity category (window period)",
    )

    # Key impact proxy: animal-care hours
    animal_care_hours_total: float = Field(
        ...,
        description="Total approved animal_care hours across all time (profile-derived proxy for animals helped)",
    )

    # Top contributors
    top_contributors: list[TopContributor] = Field(
        default_factory=list,
        description="Top 5 volunteers by all-time total_hours_logged",
    )


# ---------------------------------------------------------------------------
# Category human-readable labels
# ---------------------------------------------------------------------------

CATEGORY_LABELS: dict[str, str] = {
    HoursCategory.ANIMAL_CARE: "Cuidado animal",
    HoursCategory.VETERINARY_ASSISTANCE: "Asistencia veterinaria",
    HoursCategory.CLEANING: "Limpieza",
    HoursCategory.TRANSPORT: "Transporte",
    HoursCategory.ADMIN: "Administración",
    HoursCategory.EDUCATION_OUTREACH: "Educación / Divulgación",
    HoursCategory.EVENT: "Eventos",
    HoursCategory.FOSTER_CARE: "Cuidado temporal (foster)",
    HoursCategory.FUNDRAISING: "Recaudación de fondos",
    HoursCategory.OTHER: "Otro",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _category_breakdown(
    logs: list[VolunteerHoursLog], approved_only: bool = True
) -> list[CategoryBreakdown]:
    """Aggregate hours per category from a list of log entries."""
    totals: dict[str, float] = defaultdict(float)
    for log in logs:
        if approved_only and not log.approved:
            continue
        totals[log.category] += float(log.duration_hours or 0)

    return sorted(
        [
            CategoryBreakdown(
                category=cat,
                label=CATEGORY_LABELS.get(cat, cat),
                hours=round(hours, 2),
            )
            for cat, hours in totals.items()
            if hours > 0
        ],
        key=lambda x: x.hours,
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/impact",
    response_model=ImpactMetricsResponse,
    summary="Volunteer program impact metrics (staff only)",
)
async def get_volunteer_impact_metrics(
    window_days: int = Query(
        IMPACT_DEFAULT_WINDOW_DAYS,
        ge=1,
        le=IMPACT_MAX_WINDOW_DAYS,
        description=f"Time window for log-based metrics (1-{IMPACT_MAX_WINDOW_DAYS} days, default 30)",
    ),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> Any:
    """Return shelter-wide volunteer impact metrics.

    Combines:
    - Volunteer profile totals (all-time denormalised hours)
    - volunteer_hours_log entries within a configurable time window
    - Category breakdown of activity
    - Top 5 contributors by all-time hours

    Staff only.
    """
    today = datetime.now(UTC).date()
    window_start = today - timedelta(days=window_days - 1)

    # Load approved volunteer profiles
    profiles_result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.status == VolunteerStatus.APPROVED)
    )
    approved_profiles = list(profiles_result.scalars().all())

    total_approved = len(approved_profiles)
    total_hours_all_time = sum(float(p.total_hours_logged or 0) for p in approved_profiles)
    volunteers_with_hours = sum(
        1 for p in approved_profiles if float(p.total_hours_logged or 0) > 0
    )

    # Top 5 contributors by all-time hours
    top_5 = sorted(approved_profiles, key=lambda p: float(p.total_hours_logged or 0), reverse=True)[
        :5
    ]
    top_contributors = [
        TopContributor(
            volunteer_id=str(p.id),
            total_hours_logged=round(float(p.total_hours_logged or 0), 2),
        )
        for p in top_5
        if float(p.total_hours_logged or 0) > 0
    ]

    # Load hours log entries within the window
    logs_result = await db.execute(
        select(VolunteerHoursLog).where(VolunteerHoursLog.activity_date >= window_start)
    )
    window_logs = list(logs_result.scalars().all())

    hours_approved_window = round(
        sum(float(log.duration_hours or 0) for log in window_logs if log.approved), 2
    )
    hours_pending_window = round(
        sum(float(log.duration_hours or 0) for log in window_logs if not log.approved), 2
    )

    # All-time logs for animal_care hours (best available proxy for animals helped)
    all_logs_result = await db.execute(
        select(VolunteerHoursLog).where(
            VolunteerHoursLog.approved == True,  # noqa: E712
            VolunteerHoursLog.category == HoursCategory.ANIMAL_CARE,
        )
    )
    animal_care_logs = list(all_logs_result.scalars().all())
    animal_care_hours_total = round(
        sum(float(log.duration_hours or 0) for log in animal_care_logs), 2
    )

    category_breakdown = _category_breakdown(window_logs, approved_only=True)

    logger.info(
        "Volunteer impact metrics: approved=%d window_days=%d window_hours=%.2f",
        total_approved,
        window_days,
        hours_approved_window,
    )

    return ImpactMetricsResponse(
        generated_at=today,
        total_approved_volunteers=total_approved,
        total_volunteers_with_hours=volunteers_with_hours,
        total_hours_contributed=round(total_hours_all_time, 2),
        window_days=window_days,
        window_start=window_start,
        hours_logged_in_window=hours_approved_window,
        hours_pending_approval=hours_pending_window,
        hours_by_category=category_breakdown,
        animal_care_hours_total=animal_care_hours_total,
        top_contributors=top_contributors,
    )
