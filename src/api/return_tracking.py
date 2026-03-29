"""Return/surrender tracking and analysis API (RAP-262, EPIC-53).

Staff-only analytics endpoints for monitoring adoption returns.

Endpoints:
  GET /api/admin/returns/analytics    — aggregate return analytics
  GET /api/admin/returns/trend        — monthly return counts
  GET /api/admin/returns              — list individual return records
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.services.return_tracking_service import (
    DEFAULT_TREND_MONTHS,
    MAX_TREND_MONTHS,
    ReturnAnalytics,
    ReturnRecord,
    ReturnTrendPoint,
    get_return_analytics,
    get_return_trend,
    list_return_records,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/returns",
    tags=["return-tracking"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReturnReasonCountResponse(BaseModel):
    reason_code: str
    label: str
    count: int
    percentage: float


class ReturnAnalyticsResponse(BaseModel):
    total_returns: int
    return_rate_pct: float
    reason_breakdown: list[ReturnReasonCountResponse]
    generated_at: str


class ReturnTrendPointResponse(BaseModel):
    year: int
    month: int
    period_label: str
    return_count: int


class ReturnRecordResponse(BaseModel):
    follow_up_id: UUID
    adoption_request_id: UUID
    return_date: datetime
    return_reason_code: str | None
    return_notes: str | None


def _analytics_to_response(analytics: ReturnAnalytics) -> ReturnAnalyticsResponse:
    return ReturnAnalyticsResponse(
        total_returns=analytics.total_returns,
        return_rate_pct=analytics.return_rate_pct,
        reason_breakdown=[
            ReturnReasonCountResponse(
                reason_code=r.reason_code,
                label=r.label,
                count=r.count,
                percentage=r.percentage,
            )
            for r in analytics.reason_breakdown
        ],
        generated_at=analytics.generated_at,
    )


def _trend_to_response(point: ReturnTrendPoint) -> ReturnTrendPointResponse:
    return ReturnTrendPointResponse(
        year=point.year,
        month=point.month,
        period_label=point.period_label,
        return_count=point.return_count,
    )


def _record_to_response(record: ReturnRecord) -> ReturnRecordResponse:
    return ReturnRecordResponse(
        follow_up_id=record.follow_up_id,
        adoption_request_id=record.adoption_request_id,
        return_date=record.return_date,
        return_reason_code=record.return_reason_code,
        return_notes=record.return_notes,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/analytics",
    response_model=ReturnAnalyticsResponse,
    summary="Aggregate adoption return analytics",
)
async def return_analytics(
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> ReturnAnalyticsResponse:
    """Return aggregate return/surrender analytics.

    Includes total return count, return rate, and breakdown by reason code.

    Auth: requires staff or admin role.
    """
    analytics = await get_return_analytics(db)
    return _analytics_to_response(analytics)


@router.get(
    "/trend",
    response_model=list[ReturnTrendPointResponse],
    summary="Monthly return counts over time",
)
async def return_trend(
    months: int = Query(
        default=DEFAULT_TREND_MONTHS,
        ge=1,
        le=MAX_TREND_MONTHS,
        description=f"Lookback window in months (default: {DEFAULT_TREND_MONTHS}, max: {MAX_TREND_MONTHS})",
    ),
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[ReturnTrendPointResponse]:
    """Return monthly return counts for the last N months.

    Auth: requires staff or admin role.
    """
    points = await get_return_trend(db, months=months)
    return [_trend_to_response(p) for p in points]


@router.get(
    "",
    response_model=list[ReturnRecordResponse],
    summary="List adoption return records",
)
async def list_returns(
    reason_code: str | None = Query(default=None, description="Filter by return reason code"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _current_user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[ReturnRecordResponse]:
    """List individual adoption return records.

    Auth: requires staff or admin role.
    """
    records = await list_return_records(db, limit=limit, offset=offset, reason_code=reason_code)
    return [_record_to_response(r) for r in records]
