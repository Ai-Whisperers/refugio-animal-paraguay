"""Emergency analytics service — aggregate stats and reporting.

Provides analytics for emergency cases including summary statistics,
funding performance, time series data, and urgency distribution.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.emergency_case import EmergencyCase

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_DAYS_RANGE = 30
MAX_DAYS_RANGE = 365


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AnalyticsError(Exception):
    """Base error for analytics operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidDateRangeError(AnalyticsError):
    """Raised when date range is invalid."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message="Invalid date range",
            details=reason,
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_date_range(start_date: datetime, end_date: datetime) -> None:
    """Validate that date range is valid."""
    if start_date >= end_date:
        raise InvalidDateRangeError("Start date must be before end date")
    delta = end_date - start_date
    if delta.days > MAX_DAYS_RANGE:
        raise InvalidDateRangeError(f"Date range must not exceed {MAX_DAYS_RANGE} days")


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_emergency_summary(db: AsyncSession) -> dict:
    """Get high-level summary statistics for emergency cases.

    Returns:
        Dict with total, active, funded, closed, expired counts,
        total raised, total needed, and average funding percentage.
    """
    # Count by status
    status_counts = await db.execute(
        select(
            EmergencyCase.status,
            func.count().label("count"),
        )
        .where(EmergencyCase.is_deleted.is_(False))
        .group_by(EmergencyCase.status)
    )
    counts = {row.status: row.count for row in status_counts}

    total = sum(counts.values())

    # Funding totals
    funding_result = await db.execute(
        select(
            func.coalesce(func.sum(EmergencyCase.amount_needed_cents), 0).label("total_needed"),
            func.coalesce(func.sum(EmergencyCase.amount_raised_cents), 0).label("total_raised"),
        ).where(EmergencyCase.is_deleted.is_(False))
    )
    funding = funding_result.one()

    total_needed = funding.total_needed
    total_raised = funding.total_raised
    avg_pct = round((total_raised / total_needed) * 100, 1) if total_needed > 0 else 0

    return {
        "total_cases": total,
        "active": counts.get("active", 0),
        "funded": counts.get("funded", 0),
        "closed": counts.get("closed", 0),
        "expired": counts.get("expired", 0),
        "total_needed_cents": total_needed,
        "total_raised_cents": total_raised,
        "average_funding_percentage": avg_pct,
    }


async def get_urgency_distribution(db: AsyncSession) -> list[dict]:
    """Get distribution of emergency cases by urgency level.

    Returns:
        List of dicts with urgency, count, and average funding percentage.
    """
    result = await db.execute(
        select(
            EmergencyCase.urgency,
            func.count().label("count"),
            func.coalesce(func.sum(EmergencyCase.amount_needed_cents), 0).label("total_needed"),
            func.coalesce(func.sum(EmergencyCase.amount_raised_cents), 0).label("total_raised"),
        )
        .where(EmergencyCase.is_deleted.is_(False))
        .group_by(EmergencyCase.urgency)
    )

    distribution = []
    for row in result:
        avg_pct = (
            round((row.total_raised / row.total_needed) * 100, 1) if row.total_needed > 0 else 0
        )
        distribution.append(
            {
                "urgency": row.urgency,
                "count": row.count,
                "total_needed_cents": row.total_needed,
                "total_raised_cents": row.total_raised,
                "average_funding_percentage": avg_pct,
            }
        )

    return distribution


async def get_daily_time_series(
    db: AsyncSession,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[dict]:
    """Get daily time series of emergency case creation and funding.

    Args:
        db: Async database session.
        start_date: Start of range (defaults to 30 days ago).
        end_date: End of range (defaults to now).

    Returns:
        List of dicts with date, cases_created, total_raised_cents.

    Raises:
        InvalidDateRangeError: If date range is invalid.
    """
    now = datetime.now(UTC)
    if end_date is None:
        end_date = now
    if start_date is None:
        start_date = now - timedelta(days=DEFAULT_DAYS_RANGE)

    validate_date_range(start_date, end_date)

    date_trunc = func.date_trunc("day", EmergencyCase.created_at)
    result = await db.execute(
        select(
            date_trunc.label("day"),
            func.count().label("cases_created"),
            func.coalesce(func.sum(EmergencyCase.amount_raised_cents), 0).label("total_raised"),
        )
        .where(
            EmergencyCase.is_deleted.is_(False),
            EmergencyCase.created_at >= start_date,
            EmergencyCase.created_at <= end_date,
        )
        .group_by(date_trunc)
        .order_by(date_trunc)
    )

    return [
        {
            "date": row.day.isoformat() if row.day else None,
            "cases_created": row.cases_created,
            "total_raised_cents": row.total_raised,
        }
        for row in result
    ]


async def get_funding_performance(db: AsyncSession) -> dict:
    """Get funding performance metrics.

    Returns:
        Dict with success rate, average time to fund, and
        average funding percentage by status.
    """
    # Count funded vs total closed/funded/expired
    completed_result = await db.execute(
        select(
            EmergencyCase.status,
            func.count().label("count"),
        )
        .where(
            EmergencyCase.is_deleted.is_(False),
            EmergencyCase.status.in_(["funded", "closed", "expired"]),
        )
        .group_by(EmergencyCase.status)
    )
    completed_counts = {row.status: row.count for row in completed_result}

    total_completed = sum(completed_counts.values())
    funded_count = completed_counts.get("funded", 0) + completed_counts.get("closed", 0)
    success_rate = round((funded_count / total_completed) * 100, 1) if total_completed > 0 else 0

    # Average funding percentage across all non-deleted cases
    avg_result = await db.execute(
        select(
            func.avg(
                case(
                    (
                        EmergencyCase.amount_needed_cents > 0,
                        (
                            EmergencyCase.amount_raised_cents
                            * 100.0
                            / EmergencyCase.amount_needed_cents
                        ),
                    ),
                    else_=0,
                )
            ).label("avg_pct")
        ).where(EmergencyCase.is_deleted.is_(False))
    )
    avg_row = avg_result.one()
    avg_funding_pct = round(float(avg_row.avg_pct or 0), 1)

    return {
        "total_completed": total_completed,
        "funded_count": funded_count,
        "expired_count": completed_counts.get("expired", 0),
        "success_rate": success_rate,
        "average_funding_percentage": avg_funding_pct,
    }


async def get_top_funded_emergencies(
    db: AsyncSession,
    *,
    limit: int = 10,
) -> list[dict]:
    """Get top funded emergency cases by amount raised.

    Returns:
        List of dicts with emergency details and funding info.
    """
    result = await db.execute(
        select(EmergencyCase)
        .where(
            EmergencyCase.is_deleted.is_(False),
            EmergencyCase.amount_raised_cents > 0,
        )
        .order_by(EmergencyCase.amount_raised_cents.desc())
        .limit(limit)
    )
    cases = list(result.scalars().all())

    return [
        {
            "emergency_id": c.id,
            "title": c.title,
            "status": c.status,
            "urgency": c.urgency,
            "amount_needed_cents": c.amount_needed_cents,
            "amount_raised_cents": c.amount_raised_cents,
            "funding_percentage": (
                min(100, round((c.amount_raised_cents / c.amount_needed_cents) * 100, 1))
                if c.amount_needed_cents > 0
                else 0
            ),
            "currency": c.currency,
            "created_at": c.created_at.isoformat(),
        }
        for c in cases
    ]
