"""Emergency analytics API endpoints.

Staff-only endpoints for viewing emergency case analytics,
funding performance, and time series data.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_async_session
from src.services.emergency_analytics_service import (
    AnalyticsError,
    InvalidDateRangeError,
    get_daily_time_series,
    get_emergency_summary,
    get_funding_performance,
    get_top_funded_emergencies,
    get_urgency_distribution,
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EmergencySummaryResponse(BaseModel):
    """Emergency case summary statistics."""

    total_cases: int
    active: int
    funded: int
    closed: int
    expired: int
    total_needed_cents: int
    total_raised_cents: int
    average_funding_percentage: float


class UrgencyDistributionItem(BaseModel):
    """Urgency distribution entry."""

    urgency: str
    count: int
    total_needed_cents: int
    total_raised_cents: int
    average_funding_percentage: float


class DailyTimeSeriesItem(BaseModel):
    """Daily time series entry."""

    date: str | None
    cases_created: int
    total_raised_cents: int


class FundingPerformanceResponse(BaseModel):
    """Funding performance metrics."""

    total_completed: int
    funded_count: int
    expired_count: int
    success_rate: float
    average_funding_percentage: float


class TopFundedItem(BaseModel):
    """Top funded emergency entry."""

    emergency_id: str
    title: str
    status: str
    urgency: str
    amount_needed_cents: int
    amount_raised_cents: int
    funding_percentage: float
    currency: str
    created_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handle_analytics_error(exc: Exception) -> None:
    """Map service-layer exceptions to HTTP responses."""
    if isinstance(exc, InvalidDateRangeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, AnalyticsError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/admin/emergency-analytics",
    tags=["emergency-analytics"],
    dependencies=[Depends(require_staff)],
)


@router.get("/summary", response_model=EmergencySummaryResponse)
async def summary(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get high-level emergency case summary statistics."""
    return await get_emergency_summary(db)


@router.get(
    "/urgency-distribution",
    response_model=list[UrgencyDistributionItem],
)
async def urgency_distribution(
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Get distribution of cases by urgency level."""
    return await get_urgency_distribution(db)


@router.get(
    "/time-series",
    response_model=list[DailyTimeSeriesItem],
)
async def time_series(
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Get daily time series of emergency case creation and funding."""
    try:
        return await get_daily_time_series(
            db,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as exc:
        _handle_analytics_error(exc)
        raise


@router.get(
    "/funding-performance",
    response_model=FundingPerformanceResponse,
)
async def funding_performance(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get funding performance metrics (success rate, averages)."""
    return await get_funding_performance(db)


@router.get(
    "/top-funded",
    response_model=list[TopFundedItem],
)
async def top_funded(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """Get top funded emergency cases by amount raised."""
    return await get_top_funded_emergencies(db, limit=limit)
