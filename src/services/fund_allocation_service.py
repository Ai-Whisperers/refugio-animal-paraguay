"""Fund allocation service for expense tracking and aggregation.

Provides CRUD operations and aggregation queries for fund allocations,
including category breakdowns and period-over-period trend analysis.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.fund_allocation import FundAllocation, FundCategory


async def create_allocation(
    db: AsyncSession,
    category: FundCategory,
    amount_cents: int,
    currency: str,
    description: str,
    transaction_date: datetime,
    recorded_by_user_id: UUID | None = None,
    receipt_reference: str | None = None,
    notes: str | None = None,
) -> FundAllocation:
    """Create a new fund allocation record."""
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


async def get_allocation(
    db: AsyncSession,
    allocation_id: UUID,
) -> FundAllocation | None:
    """Get a single fund allocation by ID."""
    result = await db.execute(
        select(FundAllocation).where(FundAllocation.id == allocation_id)
    )
    return result.scalar_one_or_none()


async def update_allocation(
    db: AsyncSession,
    allocation: FundAllocation,
    updates: dict,
) -> FundAllocation:
    """Update a fund allocation with the provided fields."""
    for field, value in updates.items():
        if value is not None:
            setattr(allocation, field, value)
    await db.flush()
    await db.refresh(allocation)
    return allocation


async def delete_allocation(
    db: AsyncSession,
    allocation: FundAllocation,
) -> None:
    """Delete a fund allocation record."""
    await db.delete(allocation)
    await db.flush()


async def list_allocations(
    db: AsyncSession,
    category: FundCategory | None = None,
    currency: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[FundAllocation], int]:
    """List fund allocations with optional filters. Returns (items, total_count)."""
    query = select(FundAllocation)
    count_query = select(func.count(FundAllocation.id))

    if category is not None:
        query = query.where(FundAllocation.category == category)
        count_query = count_query.where(FundAllocation.category == category)
    if currency is not None:
        query = query.where(FundAllocation.currency == currency)
        count_query = count_query.where(FundAllocation.currency == currency)
    if start_date is not None:
        query = query.where(FundAllocation.transaction_date >= start_date)
        count_query = count_query.where(FundAllocation.transaction_date >= start_date)
    if end_date is not None:
        query = query.where(FundAllocation.transaction_date <= end_date)
        count_query = count_query.where(FundAllocation.transaction_date <= end_date)

    query = query.order_by(FundAllocation.transaction_date.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    items = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return items, total


async def get_category_breakdown(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    currency: str = "PYG",
) -> list[dict]:
    """Get fund allocation breakdown by category for a date range.

    Returns list of dicts with: category, total_cents, transaction_count, percentage.
    """
    query = (
        select(
            FundAllocation.category,
            func.sum(FundAllocation.amount_cents).label("total_cents"),
            func.count(FundAllocation.id).label("transaction_count"),
        )
        .where(
            FundAllocation.transaction_date >= start_date,
            FundAllocation.transaction_date <= end_date,
            FundAllocation.currency == currency,
        )
        .group_by(FundAllocation.category)
        .order_by(func.sum(FundAllocation.amount_cents).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    grand_total = sum(row.total_cents for row in rows) if rows else 0

    breakdown = []
    for row in rows:
        percentage = (row.total_cents / grand_total * 100) if grand_total > 0 else 0.0
        breakdown.append(
            {
                "category": row.category,
                "total_cents": row.total_cents,
                "transaction_count": row.transaction_count,
                "percentage": round(percentage, 2),
            }
        )

    return breakdown


async def get_period_trends(
    db: AsyncSession,
    current_start: datetime,
    current_end: datetime,
    previous_start: datetime,
    previous_end: datetime,
    currency: str = "PYG",
) -> list[dict]:
    """Compare fund allocations between two periods by category.

    Returns list of dicts with: category, current_period_cents,
    previous_period_cents, change_cents, change_percentage.
    """
    # Query current period
    current_query = (
        select(
            FundAllocation.category,
            func.coalesce(func.sum(FundAllocation.amount_cents), 0).label(
                "total_cents"
            ),
        )
        .where(
            FundAllocation.transaction_date >= current_start,
            FundAllocation.transaction_date <= current_end,
            FundAllocation.currency == currency,
        )
        .group_by(FundAllocation.category)
    )

    # Query previous period
    previous_query = (
        select(
            FundAllocation.category,
            func.coalesce(func.sum(FundAllocation.amount_cents), 0).label(
                "total_cents"
            ),
        )
        .where(
            FundAllocation.transaction_date >= previous_start,
            FundAllocation.transaction_date <= previous_end,
            FundAllocation.currency == currency,
        )
        .group_by(FundAllocation.category)
    )

    current_result = await db.execute(current_query)
    previous_result = await db.execute(previous_query)

    current_map = {row.category: row.total_cents for row in current_result.all()}
    previous_map = {row.category: row.total_cents for row in previous_result.all()}

    # Merge all categories from both periods
    all_categories = set(current_map.keys()) | set(previous_map.keys())

    trends = []
    for category in sorted(all_categories):
        current_cents = current_map.get(category, 0)
        previous_cents = previous_map.get(category, 0)
        change_cents = current_cents - previous_cents
        change_percentage = (
            round(change_cents / previous_cents * 100, 2)
            if previous_cents > 0
            else None
        )
        trends.append(
            {
                "category": category,
                "current_period_cents": current_cents,
                "previous_period_cents": previous_cents,
                "change_cents": change_cents,
                "change_percentage": change_percentage,
            }
        )

    return trends
