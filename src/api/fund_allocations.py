"""Fund allocations router.

Endpoints:
  POST   /fund-allocations              -- record a new expense (staff only)
  GET    /fund-allocations              -- paginated list with filters (staff only)
  GET    /fund-allocations/{id}         -- single allocation (staff only)
  PATCH  /fund-allocations/{id}         -- update allocation (staff only)
  DELETE /fund-allocations/{id}         -- delete allocation (admin only)
  GET    /fund-allocations/summary      -- category breakdown for date range (staff)
  GET    /fund-allocations/trends       -- period-over-period comparison (staff)
  GET    /fund-allocations/public       -- public transparency breakdown (no auth)
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.fund_allocation import FundCategory
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.fund_allocation import (
    CategoryBreakdown,
    FundAllocationCreate,
    FundAllocationResponse,
    FundAllocationSummary,
    FundAllocationTrends,
    FundAllocationUpdate,
)
from src.services import fund_allocation_service

router = APIRouter(prefix="/fund-allocations", tags=["fund-allocations"])


@router.get("/summary", response_model=FundAllocationSummary)
async def get_allocation_summary(
    start_date: datetime = Query(..., description="Period start (inclusive)"),
    end_date: datetime = Query(..., description="Period end (inclusive)"),
    currency: str = Query(default="PYG", pattern=r"^(EUR|PYG|USD)$"),
    _user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> FundAllocationSummary:
    """Get fund allocation breakdown by category for a date range."""
    breakdown_data = await fund_allocation_service.get_category_breakdown(
        db, start_date, end_date, currency
    )
    total = sum(item["total_cents"] for item in breakdown_data)
    breakdown = [CategoryBreakdown(**item) for item in breakdown_data]

    return FundAllocationSummary(
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        total_allocated_cents=total,
        breakdown=breakdown,
    )


@router.get("/trends", response_model=FundAllocationTrends)
async def get_allocation_trends(
    current_start: datetime = Query(..., description="Current period start"),
    current_end: datetime = Query(..., description="Current period end"),
    previous_start: datetime = Query(..., description="Previous period start"),
    previous_end: datetime = Query(..., description="Previous period end"),
    currency: str = Query(default="PYG", pattern=r"^(EUR|PYG|USD)$"),
    _user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> FundAllocationTrends:
    """Compare fund allocations between two periods."""
    trends_data = await fund_allocation_service.get_period_trends(
        db, current_start, current_end, previous_start, previous_end, currency
    )

    return FundAllocationTrends(
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
        currency=currency,
        trends=trends_data,
    )


@router.get("/public", response_model=FundAllocationSummary)
async def get_public_breakdown(
    start_date: datetime = Query(..., description="Period start (inclusive)"),
    end_date: datetime = Query(..., description="Period end (inclusive)"),
    currency: str = Query(default="PYG", pattern=r"^(EUR|PYG|USD)$"),
    db: AsyncSession = Depends(get_db),
) -> FundAllocationSummary:
    """Public transparency endpoint — category breakdown without auth.

    Shows only top-level breakdown (no vendor/recipient details).
    """
    breakdown_data = await fund_allocation_service.get_category_breakdown(
        db, start_date, end_date, currency
    )
    total = sum(item["total_cents"] for item in breakdown_data)
    breakdown = [CategoryBreakdown(**item) for item in breakdown_data]

    return FundAllocationSummary(
        start_date=start_date,
        end_date=end_date,
        currency=currency,
        total_allocated_cents=total,
        breakdown=breakdown,
    )


@router.post(
    "",
    response_model=FundAllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_allocation(
    body: FundAllocationCreate,
    user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> FundAllocationResponse:
    """Record a new fund allocation (expense)."""
    allocation = await fund_allocation_service.create_allocation(
        db=db,
        category=body.category,
        amount_cents=body.amount_cents,
        currency=body.currency,
        description=body.description,
        transaction_date=body.transaction_date,
        recorded_by_user_id=user.id,
        receipt_reference=body.receipt_reference,
        notes=body.notes,
    )
    await db.commit()
    return FundAllocationResponse.model_validate(allocation)


@router.get("", response_model=list[FundAllocationResponse])
async def list_allocations(
    category: FundCategory | None = Query(default=None),
    currency: str | None = Query(default=None, pattern=r"^(EUR|PYG|USD)$"),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> list[FundAllocationResponse]:
    """Paginated list of fund allocations with optional filters."""
    items, _total = await fund_allocation_service.list_allocations(
        db,
        category=category,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
        offset=offset,
        limit=limit,
    )
    return [FundAllocationResponse.model_validate(item) for item in items]


@router.get("/{allocation_id}", response_model=FundAllocationResponse)
async def get_allocation(
    allocation_id: UUID,
    _user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> FundAllocationResponse:
    """Get a single fund allocation by ID."""
    allocation = await fund_allocation_service.get_allocation(db, allocation_id)
    if allocation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fund allocation {allocation_id} not found",
        )
    return FundAllocationResponse.model_validate(allocation)


@router.patch("/{allocation_id}", response_model=FundAllocationResponse)
async def update_allocation(
    allocation_id: UUID,
    body: FundAllocationUpdate,
    _user: User = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
) -> FundAllocationResponse:
    """Update an existing fund allocation."""
    allocation = await fund_allocation_service.get_allocation(db, allocation_id)
    if allocation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fund allocation {allocation_id} not found",
        )

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return FundAllocationResponse.model_validate(allocation)

    allocation = await fund_allocation_service.update_allocation(
        db, allocation, updates
    )
    await db.commit()
    return FundAllocationResponse.model_validate(allocation)


@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation(
    allocation_id: UUID,
    _user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a fund allocation record. Admin only."""
    allocation = await fund_allocation_service.get_allocation(db, allocation_id)
    if allocation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fund allocation {allocation_id} not found",
        )
    await fund_allocation_service.delete_allocation(db, allocation)
    await db.commit()
