"""Service layer for driver reimbursement management.

Handles CRUD for transport expense reimbursements with status
transitions (pending -> approved/rejected -> paid).
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.driver_reimbursement import (
    VALID_EXPENSE_TYPES,
    VALID_STATUSES,
    DriverReimbursement,
    ReimbursementStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

VALID_CURRENCIES = {"PYG", "EUR", "USD"}

# Status transition rules
VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected"},
    "approved": {"paid"},
    "rejected": set(),
    "paid": set(),
}


class ReimbursementError(Exception):
    """Base error for reimbursement operations."""


class ReimbursementNotFoundError(ReimbursementError):
    """Raised when a reimbursement does not exist."""


class InvalidReimbursementError(ReimbursementError):
    """Raised when reimbursement validation fails."""


class InvalidStatusTransitionError(ReimbursementError):
    """Raised when a status transition is not allowed."""


async def create_reimbursement(
    db: AsyncSession,
    transport_request_id: UUID,
    driver_id: UUID,
    expense_type: str,
    amount: float,
    currency: str = "PYG",
    description: str | None = None,
    receipt_url: str | None = None,
) -> dict:
    """Create a new reimbursement request."""
    if expense_type not in VALID_EXPENSE_TYPES:
        raise InvalidReimbursementError(
            f"Invalid expense type '{expense_type}', must be one of {VALID_EXPENSE_TYPES}"
        )
    if currency not in VALID_CURRENCIES:
        raise InvalidReimbursementError(
            f"Invalid currency '{currency}', must be one of {VALID_CURRENCIES}"
        )
    if amount <= 0:
        raise InvalidReimbursementError("Amount must be greater than zero")

    reimbursement = DriverReimbursement(
        transport_request_id=transport_request_id,
        driver_id=driver_id,
        expense_type=expense_type,
        amount=amount,
        currency=currency,
        description=description,
        receipt_url=receipt_url,
        status=ReimbursementStatus.PENDING.value,
    )
    db.add(reimbursement)
    await db.flush()
    await db.refresh(reimbursement)

    return _reimbursement_to_dict(reimbursement)


async def get_reimbursement(db: AsyncSession, reimbursement_id: UUID) -> dict:
    """Get a reimbursement by ID."""
    result = await db.execute(
        select(DriverReimbursement).where(DriverReimbursement.id == reimbursement_id)
    )
    reimbursement = result.scalar_one_or_none()
    if reimbursement is None:
        raise ReimbursementNotFoundError(f"Reimbursement {reimbursement_id} not found")
    return _reimbursement_to_dict(reimbursement)


async def list_reimbursements(
    db: AsyncSession,
    driver_id: UUID | None = None,
    transport_request_id: UUID | None = None,
    status_filter: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict:
    """List reimbursements with optional filters."""
    base_query = select(DriverReimbursement)

    if driver_id is not None:
        base_query = base_query.where(DriverReimbursement.driver_id == driver_id)
    if transport_request_id is not None:
        base_query = base_query.where(
            DriverReimbursement.transport_request_id == transport_request_id
        )
    if status_filter is not None:
        base_query = base_query.where(DriverReimbursement.status == status_filter)

    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(DriverReimbursement.created_at.desc()).limit(limit).offset(offset)
    )
    reimbursements = list(result.scalars().all())

    return {
        "reimbursements": [_reimbursement_to_dict(r) for r in reimbursements],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def review_reimbursement(
    db: AsyncSession,
    reimbursement_id: UUID,
    reviewer_id: UUID,
    new_status: str,
    rejection_reason: str | None = None,
) -> dict:
    """Approve or reject a reimbursement."""
    result = await db.execute(
        select(DriverReimbursement).where(DriverReimbursement.id == reimbursement_id)
    )
    reimbursement = result.scalar_one_or_none()
    if reimbursement is None:
        raise ReimbursementNotFoundError(f"Reimbursement {reimbursement_id} not found")

    if new_status not in VALID_STATUSES:
        raise InvalidReimbursementError(f"Invalid status '{new_status}'")

    current = reimbursement.status
    allowed = VALID_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise InvalidStatusTransitionError(f"Cannot transition from '{current}' to '{new_status}'")

    reimbursement.status = new_status
    reimbursement.reviewed_by = reviewer_id
    reimbursement.reviewed_at = datetime.now(UTC)

    if new_status == ReimbursementStatus.REJECTED and rejection_reason:
        reimbursement.rejection_reason = rejection_reason

    await db.flush()
    await db.refresh(reimbursement)

    return _reimbursement_to_dict(reimbursement)


async def mark_paid(
    db: AsyncSession,
    reimbursement_id: UUID,
    reviewer_id: UUID,
) -> dict:
    """Mark an approved reimbursement as paid."""
    return await review_reimbursement(
        db=db,
        reimbursement_id=reimbursement_id,
        reviewer_id=reviewer_id,
        new_status=ReimbursementStatus.PAID.value,
    )


async def delete_reimbursement(db: AsyncSession, reimbursement_id: UUID) -> None:
    """Delete a reimbursement (only if pending)."""
    result = await db.execute(
        select(DriverReimbursement).where(DriverReimbursement.id == reimbursement_id)
    )
    reimbursement = result.scalar_one_or_none()
    if reimbursement is None:
        raise ReimbursementNotFoundError(f"Reimbursement {reimbursement_id} not found")

    if reimbursement.status != ReimbursementStatus.PENDING:
        raise InvalidReimbursementError(
            f"Cannot delete reimbursement with status '{reimbursement.status}'"
        )

    await db.delete(reimbursement)
    await db.flush()


def _reimbursement_to_dict(reimbursement: DriverReimbursement) -> dict:
    """Convert a DriverReimbursement to a dict."""
    return {
        "id": reimbursement.id,
        "transport_request_id": reimbursement.transport_request_id,
        "driver_id": reimbursement.driver_id,
        "expense_type": reimbursement.expense_type,
        "amount": reimbursement.amount,
        "currency": reimbursement.currency,
        "description": reimbursement.description,
        "receipt_url": reimbursement.receipt_url,
        "status": reimbursement.status,
        "reviewed_by": reimbursement.reviewed_by,
        "reviewed_at": reimbursement.reviewed_at,
        "rejection_reason": reimbursement.rejection_reason,
        "created_at": reimbursement.created_at,
        "updated_at": reimbursement.updated_at,
    }
