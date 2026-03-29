"""Service layer for adoption return/surrender tracking and analysis (RAP-262, EPIC-53).

Provides analytics on adoption returns: rates, trends, reason breakdowns,
and per-animal return history. Draws data from the FollowUp table where
return_date is set.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.follow_up import FollowUp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TREND_MONTHS = 12
MAX_TREND_MONTHS = 36

REASON_LABELS: dict[str, str] = {
    "moved_away": "Moved away",
    "behavior_issues": "Behaviour issues",
    "family_circumstances": "Family circumstances",
    "allergies": "Allergies",
    "housing_situation": "Housing situation",
    "financial": "Financial",
    "time_constraints": "Time constraints",
    "other": "Other",
}

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReturnReasonCount:
    """Count of returns for a single reason code."""

    reason_code: str
    label: str
    count: int
    percentage: float


@dataclass(frozen=True)
class ReturnTrendPoint:
    """Monthly return count data point."""

    year: int
    month: int
    period_label: str
    return_count: int


@dataclass(frozen=True)
class ReturnAnalytics:
    """Aggregated return/surrender analytics."""

    total_returns: int
    return_rate_pct: float
    reason_breakdown: list[ReturnReasonCount]
    generated_at: str


@dataclass(frozen=True)
class ReturnRecord:
    """Single return record for an adoption."""

    follow_up_id: UUID
    adoption_request_id: UUID
    return_date: datetime
    return_reason_code: str | None
    return_notes: str | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_pct(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total * 100, 2)


def _month_label(year: int, month: int) -> str:
    """Return a short period label like 'Mar 2026'."""
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    return f"{month_names[month - 1]} {year}"


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_return_analytics(db: AsyncSession) -> ReturnAnalytics:
    """Return aggregated analytics for all adoption returns.

    Includes total return count, per-reason breakdown, and return rate
    against total completed follow-ups (proxy for total adoptions tracked).
    """
    # Total returns (follow-ups with a return_date set)
    total_result = await db.execute(
        select(func.count(FollowUp.id)).where(FollowUp.return_date.is_not(None))
    )
    total_returns = int(total_result.scalar_one())

    # Total follow-ups as denominator for rate
    total_fu_result = await db.execute(select(func.count(FollowUp.id)))
    total_follow_ups = int(total_fu_result.scalar_one())

    # Reason breakdown
    reason_result = await db.execute(
        select(
            FollowUp.return_reason_code,
            func.count(FollowUp.id).label("count"),
        )
        .where(FollowUp.return_date.is_not(None))
        .group_by(FollowUp.return_reason_code)
        .order_by(func.count(FollowUp.id).desc())
    )
    reason_rows = reason_result.fetchall()

    reason_breakdown = [
        ReturnReasonCount(
            reason_code=row.return_reason_code or "unknown",
            label=REASON_LABELS.get(row.return_reason_code or "", "Unknown"),
            count=int(row.count),
            percentage=_safe_pct(int(row.count), total_returns),
        )
        for row in reason_rows
    ]

    return ReturnAnalytics(
        total_returns=total_returns,
        return_rate_pct=_safe_pct(total_returns, total_follow_ups),
        reason_breakdown=reason_breakdown,
        generated_at=datetime.now(UTC).isoformat(),
    )


async def get_return_trend(
    db: AsyncSession,
    months: int = DEFAULT_TREND_MONTHS,
) -> list[ReturnTrendPoint]:
    """Return monthly return counts for the last `months` months.

    Results are ordered chronologically (oldest first).
    """
    cutoff = datetime.now(UTC) - timedelta(days=months * 30)

    result = await db.execute(
        select(
            func.extract("year", FollowUp.return_date).label("year"),
            func.extract("month", FollowUp.return_date).label("month"),
            func.count(FollowUp.id).label("return_count"),
        )
        .where(
            FollowUp.return_date.is_not(None),
            FollowUp.return_date >= cutoff,
        )
        .group_by("year", "month")
        .order_by("year", "month")
    )
    rows = result.fetchall()

    return [
        ReturnTrendPoint(
            year=int(row.year),
            month=int(row.month),
            period_label=_month_label(int(row.year), int(row.month)),
            return_count=int(row.return_count),
        )
        for row in rows
    ]


async def list_return_records(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    reason_code: str | None = None,
) -> list[ReturnRecord]:
    """List individual return records with optional reason code filter."""
    query = (
        select(FollowUp)
        .where(FollowUp.return_date.is_not(None))
        .order_by(FollowUp.return_date.desc())
    )
    if reason_code is not None:
        query = query.where(FollowUp.return_reason_code == reason_code)
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return [
        ReturnRecord(
            follow_up_id=fu.id,
            adoption_request_id=fu.adoption_request_id,
            return_date=fu.return_date,  # type: ignore[arg-type] — filtered by is_not(None)
            return_reason_code=fu.return_reason_code,
            return_notes=fu.return_notes,
        )
        for fu in result.scalars()
    ]
