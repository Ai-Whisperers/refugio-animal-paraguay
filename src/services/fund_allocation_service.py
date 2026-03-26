"""Service layer for fund allocation tracking and transparency reporting."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donation, DonationStatus
from src.db.models.fund_allocation import FundAllocation


async def create_allocation(
    db: AsyncSession,
    category: str,
    amount_cents: int,
    currency: str,
    description: str,
    transaction_date: datetime,
    recorded_by_user_id: UUID | None = None,
    receipt_reference: str | None = None,
    notes: str | None = None,
) -> FundAllocation:
    """Record a new fund allocation (expense)."""
    allocation = FundAllocation(
        category=category,
        amount_cents=amount_cents,
        currency=currency,
        description=description,
        transaction_date=transaction_date,
        recorded_by_user_id=recorded_by_user_id,
        receipt_reference=receipt_reference,
        notes=notes,
    )
    db.add(allocation)
    await db.flush()
    await db.refresh(allocation)
    return allocation


async def get_allocation_breakdown(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    currency: str = "PYG",
) -> dict:
    """Calculate fund allocation breakdown by category for a date range."""
    expense_q = await db.execute(
        select(
            FundAllocation.category,
            func.sum(FundAllocation.amount_cents).label("total_cents"),
            func.count().label("transaction_count"),
        )
        .where(
            FundAllocation.transaction_date >= start_date,
            FundAllocation.transaction_date <= end_date,
            FundAllocation.currency == currency,
        )
        .group_by(FundAllocation.category)
        .order_by(func.sum(FundAllocation.amount_cents).desc())
    )

    categories = []
    total_expenses = 0
    for row in expense_q:
        total_expenses += row.total_cents
        categories.append(
            {
                "category": row.category,
                "total_cents": row.total_cents,
                "transaction_count": row.transaction_count,
            }
        )

    breakdown = []
    for cat in categories:
        pct = round(cat["total_cents"] / total_expenses * 100, 1) if total_expenses > 0 else 0.0
        breakdown.append(
            {
                "category": cat["category"],
                "total_cents": cat["total_cents"],
                "percentage": pct,
                "transaction_count": cat["transaction_count"],
            }
        )

    donations_q = await db.execute(
        select(func.coalesce(func.sum(Donation.amount_cents), 0)).where(
            Donation.created_at >= start_date,
            Donation.created_at <= end_date,
            Donation.currency == currency,
            Donation.status == DonationStatus.COMPLETED.value,
        )
    )
    total_donations = donations_q.scalar_one()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_expenses_cents": total_expenses,
        "total_donations_cents": total_donations,
        "currency": currency,
        "breakdown": breakdown,
    }
