"""Fund allocation (expense tracking) router.

Endpoints:
  GET    /fund-allocations                    - list allocations (filter by category/date)
  GET    /fund-allocations/{id}               - single allocation detail
  POST   /fund-allocations                    - record new expense
  GET    /fund-allocations/summary             - allocation breakdown by category
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.fund_allocation import FundAllocation
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.fund_allocation import (
    FundAllocationCreate,
    FundAllocationResponse,
    FundAllocationSummary,
)
from src.services.fund_allocation_service import (
    create_allocation,
    get_allocation_breakdown,
)

router = APIRouter(prefix="/fund-allocations", tags=["fund-allocations"], responses=RESOURCE_RESPONSES)

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


@router.get("/summary", response_model=FundAllocationSummary)
async def allocation_summary(
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    currency: str = Query(default="PYG", max_length=3),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> dict:
    """Get fund allocation breakdown by category for a date range.

    Defaults to last 12 months if no dates provided.
    """
    if end_date is None:
        end_date = datetime.now(UTC)
    if start_date is None:
        start_date = end_date - timedelta(days=365)

    return await get_allocation_breakdown(db, start_date, end_date, currency)


@router.get("", response_model=list[FundAllocationResponse])
async def list_allocations(
    category: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[FundAllocation]:
    """List fund allocations with optional category filter."""
    stmt = (
        select(FundAllocation)
        .offset(offset)
        .limit(limit)
        .order_by(FundAllocation.transaction_date.desc())
    )
    if category is not None:
        stmt = stmt.where(FundAllocation.category == category)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{allocation_id}", response_model=FundAllocationResponse)
async def get_allocation(
    allocation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> FundAllocation:
    """Get a single fund allocation by ID."""
    allocation = await db.get(FundAllocation, allocation_id)
    if allocation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund allocation not found",
        )
    return allocation


@router.post(
    "",
    response_model=FundAllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_fund_allocation(
    payload: FundAllocationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> FundAllocation:
    """Record a new fund allocation (expense)."""
    return await create_allocation(
        db,
        category=payload.category.value,
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        description=payload.description,
        transaction_date=payload.transaction_date,
        recorded_by_user_id=current_user.id,
        receipt_reference=payload.receipt_reference,
        notes=payload.notes,
    )
