"""Service for managing donation allocations and expenses.

Handles creating expenses, allocating donations to expenses,
and computing allocation statistics.
"""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donation
from src.db.models.expense import DonationAllocation, Expense, ExpenseCategory

logger = logging.getLogger(__name__)

# Allocation constraints
MIN_DESCRIPTION_LENGTH = 5
MAX_DESCRIPTION_LENGTH = 500
MIN_NOTE_LENGTH = 0
MAX_NOTE_LENGTH = 500


class ExpenseNotFoundError(Exception):
    """Raised when an expense is not found."""

    def __init__(self, expense_id: UUID) -> None:
        self.expense_id = expense_id
        self.message = f"Expense {expense_id} not found."
        super().__init__(self.message)


class DonationNotFoundError(Exception):
    """Raised when a donation is not found."""

    def __init__(self, donation_id: UUID) -> None:
        self.donation_id = donation_id
        self.message = f"Donation {donation_id} not found."
        super().__init__(self.message)


class AllocationExceedsDonationError(Exception):
    """Raised when allocation would exceed donation amount."""

    def __init__(self, donation_id: UUID, available_cents: int, requested_cents: int) -> None:
        self.donation_id = donation_id
        self.available_cents = available_cents
        self.requested_cents = requested_cents
        self.message = (
            f"Allocation of {requested_cents} cents exceeds available "
            f"{available_cents} cents for donation {donation_id}."
        )
        super().__init__(self.message)


class InvalidExpenseError(Exception):
    """Raised when expense data is invalid."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        self.message = f"Invalid expense: {reason}"
        super().__init__(self.message)


def validate_expense_data(
    description: str,
    category: str,
    amount_cents: int,
    expense_date: date,
) -> None:
    """Validate expense creation data.

    Raises InvalidExpenseError if validation fails.
    """
    if len(description) < MIN_DESCRIPTION_LENGTH:
        raise InvalidExpenseError(
            f"Description must be at least {MIN_DESCRIPTION_LENGTH} characters."
        )
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise InvalidExpenseError(
            f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
        )

    valid_categories = {c.value for c in ExpenseCategory}
    if category not in valid_categories:
        raise InvalidExpenseError(
            f"Unknown category '{category}'. Valid: {sorted(valid_categories)}"
        )

    if amount_cents <= 0:
        raise InvalidExpenseError("Amount must be positive.")

    if expense_date > date.today():
        raise InvalidExpenseError("Expense date cannot be in the future.")


async def create_expense(
    db: AsyncSession,
    description: str,
    category: str,
    amount_cents: int,
    currency: str,
    expense_date: date,
    related_animal_id: UUID | None = None,
    recorded_by_id: UUID | None = None,
    notes: str | None = None,
) -> Expense:
    """Create a new expense record."""
    validate_expense_data(description, category, amount_cents, expense_date)

    expense = Expense(
        description=description,
        category=category,
        amount_cents=amount_cents,
        currency=currency,
        expense_date=expense_date,
        related_animal_id=related_animal_id,
        recorded_by_id=recorded_by_id,
        notes=notes,
    )
    db.add(expense)
    await db.flush()
    await db.refresh(expense)
    return expense


async def get_expense(db: AsyncSession, expense_id: UUID) -> Expense:
    """Get an expense by ID or raise."""
    expense = await db.get(Expense, expense_id)
    if expense is None:
        raise ExpenseNotFoundError(expense_id)
    return expense


async def list_expenses(
    db: AsyncSession,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Expense]:
    """List expenses with optional filters."""
    stmt = select(Expense)
    if category is not None:
        stmt = stmt.where(Expense.category == category)
    if date_from is not None:
        stmt = stmt.where(Expense.expense_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Expense.expense_date <= date_to)
    stmt = stmt.order_by(Expense.expense_date.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_donation_allocated_amount(db: AsyncSession, donation_id: UUID) -> int:
    """Get the total amount already allocated from a donation."""
    stmt = select(func.coalesce(func.sum(DonationAllocation.amount_cents), 0)).where(
        DonationAllocation.donation_id == donation_id
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def allocate_donation(
    db: AsyncSession,
    donation_id: UUID,
    expense_id: UUID,
    amount_cents: int,
    note: str | None = None,
) -> DonationAllocation:
    """Allocate part or all of a donation to an expense.

    Validates that:
    1. Donation exists
    2. Expense exists
    3. Allocation amount doesn't exceed remaining unallocated amount

    Returns the created DonationAllocation.
    """
    # Verify donation exists
    donation = await db.get(Donation, donation_id)
    if donation is None:
        raise DonationNotFoundError(donation_id)

    # Verify expense exists
    await get_expense(db, expense_id)

    if amount_cents <= 0:
        raise InvalidExpenseError("Allocation amount must be positive.")

    # Check remaining unallocated amount
    already_allocated = await get_donation_allocated_amount(db, donation_id)
    available = donation.amount_cents - already_allocated
    if amount_cents > available:
        raise AllocationExceedsDonationError(donation_id, available, amount_cents)

    allocation = DonationAllocation(
        donation_id=donation_id,
        expense_id=expense_id,
        amount_cents=amount_cents,
        note=note,
    )
    db.add(allocation)
    await db.flush()
    await db.refresh(allocation)
    return allocation


async def get_donation_allocations(
    db: AsyncSession,
    donation_id: UUID,
) -> list[DonationAllocation]:
    """Get all allocations for a donation."""
    stmt = (
        select(DonationAllocation)
        .where(DonationAllocation.donation_id == donation_id)
        .order_by(DonationAllocation.allocated_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_allocation_stats(db: AsyncSession) -> dict:
    """Get overall donation allocation statistics.

    Returns:
    - total_donations_cents: sum of all completed donations
    - total_allocated_cents: sum of all allocations
    - allocation_rate: percentage of donations allocated
    - unallocated_count: number of donations with no allocations
    - total_expenses: count of expenses
    - allocations_by_category: breakdown by expense category
    """
    # Total completed donations
    total_donations_stmt = select(func.coalesce(func.sum(Donation.amount_cents), 0)).where(
        Donation.status == "completed"
    )
    total_donations_result = await db.execute(total_donations_stmt)
    total_donations_cents: int = total_donations_result.scalar_one()

    # Total allocated
    total_allocated_stmt = select(func.coalesce(func.sum(DonationAllocation.amount_cents), 0))
    total_allocated_result = await db.execute(total_allocated_stmt)
    total_allocated_cents: int = total_allocated_result.scalar_one()

    # Allocation rate
    allocation_rate = (
        round((total_allocated_cents / total_donations_cents) * 100, 1)
        if total_donations_cents > 0
        else 0.0
    )

    # Unallocated donation count (completed donations with no allocations)
    allocated_donation_ids = select(DonationAllocation.donation_id).distinct()
    unallocated_stmt = select(func.count(Donation.id)).where(
        Donation.status == "completed",
        Donation.id.notin_(allocated_donation_ids),
    )
    unallocated_result = await db.execute(unallocated_stmt)
    unallocated_count: int = unallocated_result.scalar_one()

    # Total expenses
    expense_count_stmt = select(func.count(Expense.id))
    expense_count_result = await db.execute(expense_count_stmt)
    total_expenses: int = expense_count_result.scalar_one()

    # Allocations by category
    category_stmt = (
        select(
            Expense.category,
            func.count(DonationAllocation.id).label("allocation_count"),
            func.sum(DonationAllocation.amount_cents).label("total_cents"),
        )
        .join(DonationAllocation, DonationAllocation.expense_id == Expense.id)
        .group_by(Expense.category)
        .order_by(Expense.category)
    )
    category_result = await db.execute(category_stmt)
    allocations_by_category = {
        row.category: {
            "count": row.allocation_count,
            "total_cents": row.total_cents or 0,
        }
        for row in category_result.all()
    }

    return {
        "total_donations_cents": total_donations_cents,
        "total_allocated_cents": total_allocated_cents,
        "allocation_rate": allocation_rate,
        "unallocated_count": unallocated_count,
        "total_expenses": total_expenses,
        "allocations_by_category": allocations_by_category,
    }
