"""Endpoints for donation allocation and expense management.

Endpoints:
    POST /admin/expenses                          -- create expense record
    GET  /admin/expenses                          -- list expenses
    GET  /admin/expenses/{id}                     -- get expense detail
    POST /admin/donations/{id}/allocate           -- allocate donation to expense
    GET  /api/donations/{id}/allocation           -- get donation allocations
    GET  /admin/donation-allocations/stats        -- allocation statistics
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.expense import ExpenseCategory
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.services.donation_allocation_service import (
    AllocationExceedsDonationError,
    DonationNotFoundError,
    ExpenseNotFoundError,
    InvalidExpenseError,
    allocate_donation,
    create_expense,
    get_allocation_stats,
    get_donation_allocations,
    get_expense,
    list_expenses,
)

logger = logging.getLogger(__name__)


# --- Schemas ---


class CreateExpenseRequest(BaseModel):
    """Request body for creating an expense."""

    description: str = Field(..., min_length=5, max_length=500)
    category: ExpenseCategory
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="PYG", max_length=3)
    expense_date: date
    related_animal_id: UUID | None = None
    notes: str | None = None


class ExpenseResponse(BaseModel):
    """Response for an expense record."""

    model_config = {"from_attributes": True}

    id: UUID
    description: str
    category: str
    amount_cents: int
    currency: str
    expense_date: date
    related_animal_id: UUID | None
    recorded_by_id: UUID | None
    notes: str | None


class AllocateDonationRequest(BaseModel):
    """Request body for allocating a donation to an expense."""

    expense_id: UUID
    amount_cents: int = Field(..., gt=0)
    note: str | None = Field(default=None, max_length=500)


class AllocationResponse(BaseModel):
    """Response for a donation allocation."""

    model_config = {"from_attributes": True}

    id: UUID
    donation_id: UUID
    expense_id: UUID
    amount_cents: int
    note: str | None
    allocated_at: str


class DonationAllocationListResponse(BaseModel):
    """List of allocations for a donation."""

    donation_id: UUID
    total_allocated_cents: int
    allocations: list[AllocationResponse]


class CategoryBreakdown(BaseModel):
    """Allocation breakdown for a single expense category."""

    count: int
    total_cents: int


class AllocationStatsResponse(BaseModel):
    """Overall donation allocation statistics."""

    total_donations_cents: int
    total_allocated_cents: int
    allocation_rate: float
    unallocated_count: int
    total_expenses: int
    allocations_by_category: dict[str, CategoryBreakdown]


# --- Routers ---

expense_router = APIRouter(
    prefix="/admin/expenses",
    tags=["expenses"],
    responses=RESOURCE_RESPONSES,
)

allocation_router = APIRouter(
    tags=["donation-allocations"],
    responses=RESOURCE_RESPONSES,
)


# --- Expense Endpoints ---


@expense_router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense_endpoint(
    body: CreateExpenseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> ExpenseResponse:
    """Create a new expense record. Staff only."""
    try:
        expense = await create_expense(
            db,
            description=body.description,
            category=body.category.value,
            amount_cents=body.amount_cents,
            currency=body.currency,
            expense_date=body.expense_date,
            related_animal_id=body.related_animal_id,
            recorded_by_id=current_user.id,
            notes=body.notes,
        )
    except InvalidExpenseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None

    await db.commit()
    return ExpenseResponse.model_validate(expense)


@expense_router.get("", response_model=list[ExpenseResponse])
async def list_expenses_endpoint(
    category: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list[ExpenseResponse]:
    """List expenses with optional filters. Staff only."""
    expenses = await list_expenses(db, category=category, date_from=date_from, date_to=date_to)
    return [ExpenseResponse.model_validate(e) for e in expenses]


@expense_router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense_endpoint(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ExpenseResponse:
    """Get a single expense by ID. Staff only."""
    try:
        expense = await get_expense(db, expense_id)
    except ExpenseNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense {expense_id} not found.",
        ) from None

    return ExpenseResponse.model_validate(expense)


# --- Allocation Endpoints ---


@allocation_router.post(
    "/admin/donations/{donation_id}/allocate",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def allocate_donation_endpoint(
    donation_id: UUID,
    body: AllocateDonationRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> AllocationResponse:
    """Allocate a donation to an expense. Admin only."""
    try:
        allocation = await allocate_donation(
            db,
            donation_id=donation_id,
            expense_id=body.expense_id,
            amount_cents=body.amount_cents,
            note=body.note,
        )
    except DonationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None
    except ExpenseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from None
    except AllocationExceedsDonationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None
    except InvalidExpenseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None

    await db.commit()
    return AllocationResponse(
        id=allocation.id,
        donation_id=allocation.donation_id,
        expense_id=allocation.expense_id,
        amount_cents=allocation.amount_cents,
        note=allocation.note,
        allocated_at=allocation.allocated_at.isoformat(),
    )


@allocation_router.get(
    "/api/donations/{donation_id}/allocation",
    response_model=DonationAllocationListResponse,
)
async def get_donation_allocation_endpoint(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> DonationAllocationListResponse:
    """Get allocation details for a donation. Staff only."""
    allocations = await get_donation_allocations(db, donation_id)
    total_allocated = sum(a.amount_cents for a in allocations)

    return DonationAllocationListResponse(
        donation_id=donation_id,
        total_allocated_cents=total_allocated,
        allocations=[
            AllocationResponse(
                id=a.id,
                donation_id=a.donation_id,
                expense_id=a.expense_id,
                amount_cents=a.amount_cents,
                note=a.note,
                allocated_at=a.allocated_at.isoformat(),
            )
            for a in allocations
        ],
    )


@allocation_router.get(
    "/admin/donation-allocations/stats",
    response_model=AllocationStatsResponse,
)
async def get_allocation_stats_endpoint(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> AllocationStatsResponse:
    """Get allocation statistics dashboard. Admin only."""
    stats = await get_allocation_stats(db)
    return AllocationStatsResponse(
        total_donations_cents=stats["total_donations_cents"],
        total_allocated_cents=stats["total_allocated_cents"],
        allocation_rate=stats["allocation_rate"],
        unallocated_count=stats["unallocated_count"],
        total_expenses=stats["total_expenses"],
        allocations_by_category={
            k: CategoryBreakdown(**v) for k, v in stats["allocations_by_category"].items()
        },
    )
