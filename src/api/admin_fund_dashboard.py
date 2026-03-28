"""Admin fund management dashboard API endpoint.

Endpoints:
  GET /admin/funds/dashboard  - Comprehensive fund overview for admin dashboard
  GET /admin/funds/trending   - Donation trending data (daily/weekly/monthly)
  GET /admin/funds/export     - CSV export of donation data
"""

import csv
import io
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.donation import Donation
from src.db.models.expense import DonationAllocation
from src.db.models.user import User
from src.db.session import get_db
from src.services.donation_allocation_service import get_allocation_stats

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/funds",
    tags=["admin-fund-dashboard"],
)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TargetTypeBreakdown(BaseModel):
    """Donation breakdown for a single target type."""

    target_type: str
    count: int
    total_cents: int


class TrendingPoint(BaseModel):
    """A single data point in the donation trending chart."""

    period: str  # "2026-03-28" for daily, "2026-W13" for weekly, "2026-03" for monthly
    count: int
    total_cents: int


class FundDashboardResponse(BaseModel):
    """Comprehensive fund dashboard data."""

    # Core stats (from allocation service)
    total_donations_cents: int
    total_allocated_cents: int
    unallocated_cents: int
    allocation_rate: float
    unallocated_count: int
    total_expenses: int

    # Breakdown by target type
    by_target_type: list[TargetTypeBreakdown]

    # Fund health
    health_status: str  # "healthy", "warning", "critical"
    health_message: str

    # Quick counts
    total_donation_count: int
    pending_allocation_count: int


class TrendingResponse(BaseModel):
    """Donation trending data."""

    granularity: str  # "daily", "weekly", "monthly"
    data: list[TrendingPoint]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=FundDashboardResponse)
async def get_fund_dashboard(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> FundDashboardResponse:
    """Get comprehensive fund management dashboard data. Admin only."""
    # Get core stats from existing service
    stats = await get_allocation_stats(db)

    total_donations_cents = stats["total_donations_cents"]
    total_allocated_cents = stats["total_allocated_cents"]
    unallocated_cents = max(0, total_donations_cents - total_allocated_cents)

    # Breakdown by target type
    target_stmt = (
        select(
            Donation.target_type,
            func.count(Donation.id).label("count"),
            func.coalesce(func.sum(Donation.amount_cents), 0).label("total_cents"),
        )
        .where(Donation.status == "completed")
        .group_by(Donation.target_type)
        .order_by(func.sum(Donation.amount_cents).desc())
    )
    target_result = await db.execute(target_stmt)
    by_target_type = [
        TargetTypeBreakdown(
            target_type=row.target_type or "general",
            count=row.count,
            total_cents=int(row.total_cents),
        )
        for row in target_result.all()
    ]

    # Total donation count
    count_stmt = select(func.count(Donation.id)).where(Donation.status == "completed")
    count_result = await db.execute(count_stmt)
    total_donation_count = count_result.scalar_one()

    # Pending allocation count = donations with no allocations
    pending_allocation_count = stats["unallocated_count"]

    # Fund health assessment
    allocation_rate = stats["allocation_rate"]
    if allocation_rate >= 80:
        health_status = "healthy"
        health_message = "Los fondos se estan asignando adecuadamente."
    elif allocation_rate >= 50:
        health_status = "warning"
        health_message = (
            "Asigne fondos regularmente para mantener la transparencia. "
            f"Tasa actual: {allocation_rate:.1f}%"
        )
    else:
        health_status = "critical"
        health_message = (
            f"Mas del {100 - allocation_rate:.0f}% de las donaciones no han sido asignadas. "
            "Se recomienda asignar fondos lo antes posible."
        )

    return FundDashboardResponse(
        total_donations_cents=total_donations_cents,
        total_allocated_cents=total_allocated_cents,
        unallocated_cents=unallocated_cents,
        allocation_rate=allocation_rate,
        unallocated_count=stats["unallocated_count"],
        total_expenses=stats["total_expenses"],
        by_target_type=by_target_type,
        health_status=health_status,
        health_message=health_message,
        total_donation_count=total_donation_count,
        pending_allocation_count=pending_allocation_count,
    )


@router.get("/trending", response_model=TrendingResponse)
async def get_donation_trending(
    granularity: str = Query(
        default="daily",
        description="Grouping: daily, weekly, monthly",
        pattern="^(daily|weekly|monthly)$",
    ),
    days: int = Query(default=90, ge=7, le=365, description="Lookback days"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> TrendingResponse:
    """Get donation trending data for chart visualization. Admin only."""
    start_date = date.today() - timedelta(days=days)

    if granularity == "daily":
        period_expr = cast(Donation.created_at, sa_date_type())
        format_fn = lambda d: str(d)  # noqa: E731
    elif granularity == "weekly":
        period_expr = func.date_trunc("week", Donation.created_at)
        format_fn = lambda d: (
            d.strftime("%Y-W%V") if hasattr(d, "strftime") else str(d)
        )
    else:  # monthly
        period_expr = func.date_trunc("month", Donation.created_at)
        format_fn = lambda d: (
            d.strftime("%Y-%m") if hasattr(d, "strftime") else str(d)
        )

    stmt = (
        select(
            period_expr.label("period"),
            func.count(Donation.id).label("count"),
            func.coalesce(func.sum(Donation.amount_cents), 0).label("total_cents"),
        )
        .where(
            Donation.status == "completed",
            Donation.created_at >= start_date,
        )
        .group_by("period")
        .order_by("period")
    )
    result = await db.execute(stmt)
    data = [
        TrendingPoint(
            period=format_fn(row.period),
            count=row.count,
            total_cents=int(row.total_cents),
        )
        for row in result.all()
    ]

    return TrendingResponse(granularity=granularity, data=data)


@router.get("/export")
async def export_fund_report(
    date_from: date | None = Query(None, description="Start date filter"),
    date_to: date | None = Query(None, description="End date filter"),
    target_type: str | None = Query(None, description="Filter by target type"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> StreamingResponse:
    """Export fund report as CSV. Admin only."""
    stmt = select(Donation).where(Donation.status == "completed")
    if date_from:
        stmt = stmt.where(Donation.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Donation.created_at <= date_to)
    if target_type:
        stmt = stmt.where(Donation.target_type == target_type)
    stmt = stmt.order_by(Donation.created_at.desc())

    result = await db.execute(stmt)
    donations = result.scalars().all()

    # Get allocation totals per donation
    alloc_stmt = select(
        DonationAllocation.donation_id,
        func.sum(DonationAllocation.amount_cents).label("allocated_cents"),
    ).group_by(DonationAllocation.donation_id)
    alloc_result = await db.execute(alloc_stmt)
    alloc_map = {row.donation_id: row.allocated_cents for row in alloc_result.all()}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "date",
            "donation_id",
            "donor_id",
            "amount_cents",
            "currency",
            "target_type",
            "target_id",
            "allocation_status",
            "allocated_cents",
        ]
    )

    for d in donations:
        allocated = alloc_map.get(d.id, 0) or 0
        if allocated >= d.amount_cents:
            alloc_status = "fully_allocated"
        elif allocated > 0:
            alloc_status = "partially_allocated"
        else:
            alloc_status = "unallocated"

        writer.writerow(
            [
                d.created_at.strftime("%Y-%m-%d") if d.created_at else "",
                str(d.id),
                str(d.donor_id) if d.donor_id else "",
                d.amount_cents,
                d.currency,
                d.target_type or "general",
                str(d.target_id) if d.target_id else "",
                alloc_status,
                allocated,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fund_report.csv"},
    )


def sa_date_type():
    """Return SQLAlchemy Date type for casting."""
    import sqlalchemy as sa

    return sa.Date
