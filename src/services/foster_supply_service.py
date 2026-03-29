"""Foster supply request service (RAP-194).

Provides CRUD and lifecycle management for FosterSupplyRequest records.
Foster families submit requests; staff approve, fulfil, or reject them.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.foster_supply_request import (
    FosterSupplyRequest,
    SupplyRequestStatus,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Foster-family-facing operations
# ---------------------------------------------------------------------------


async def create_supply_request(
    db: AsyncSession,
    foster_profile_id: UUID,
    supply_type: str,
    description: str,
    quantity: int | None = None,
    placement_id: UUID | None = None,
) -> FosterSupplyRequest:
    """Create a new supply request on behalf of a foster family.

    The request starts in PENDING status.  No business-rule validation is
    performed here beyond DB constraints — callers should validate field values
    before invoking this function.
    """
    req = FosterSupplyRequest(
        foster_profile_id=foster_profile_id,
        placement_id=placement_id,
        supply_type=supply_type,
        description=description,
        quantity=quantity,
        status=SupplyRequestStatus.PENDING,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)

    logger.info(
        "Foster supply request created",
        extra={
            "supply_request_id": str(req.id),
            "foster_profile_id": str(foster_profile_id),
            "supply_type": supply_type,
        },
    )
    return req


async def list_requests_for_foster(
    db: AsyncSession,
    foster_profile_id: UUID,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[FosterSupplyRequest], int]:
    """Return paginated supply requests for a specific foster profile."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    count_stmt = (
        select(func.count())
        .select_from(FosterSupplyRequest)
        .where(FosterSupplyRequest.foster_profile_id == foster_profile_id)
    )
    total: int = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        select(FosterSupplyRequest)
        .where(FosterSupplyRequest.foster_profile_id == foster_profile_id)
        .order_by(FosterSupplyRequest.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = await db.execute(items_stmt)
    return list(rows.scalars().all()), total


# ---------------------------------------------------------------------------
# Staff-facing operations
# ---------------------------------------------------------------------------


async def list_all_requests(
    db: AsyncSession,
    status_filter: str | None = None,
    supply_type_filter: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[FosterSupplyRequest], int]:
    """Return paginated supply requests, optionally filtered by status and type."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    base_clause = []
    if status_filter:
        base_clause.append(FosterSupplyRequest.status == status_filter)
    if supply_type_filter:
        base_clause.append(FosterSupplyRequest.supply_type == supply_type_filter)

    count_stmt = select(func.count()).select_from(FosterSupplyRequest)
    items_stmt = select(FosterSupplyRequest)
    for clause in base_clause:
        count_stmt = count_stmt.where(clause)
        items_stmt = items_stmt.where(clause)

    total: int = (await db.execute(count_stmt)).scalar_one()

    items_stmt = (
        items_stmt.order_by(FosterSupplyRequest.created_at.desc()).offset(offset).limit(page_size)
    )
    rows = await db.execute(items_stmt)
    return list(rows.scalars().all()), total


async def fulfill_request(
    db: AsyncSession,
    request_id: UUID,
    resolved_by: UUID,
    staff_notes: str | None = None,
) -> FosterSupplyRequest:
    """Mark a supply request as fulfilled.

    Raises:
        ValueError: if not found or not in a fulfillable status.
    """
    req = await _get_or_raise(db, request_id)

    if req.status == SupplyRequestStatus.FULFILLED:
        raise ValueError(f"Supply request {request_id} is already fulfilled")

    if req.status == SupplyRequestStatus.REJECTED:
        raise ValueError(f"Supply request {request_id} has been rejected and cannot be fulfilled")

    now = datetime.now(tz=UTC)
    req.status = SupplyRequestStatus.FULFILLED
    req.resolved_at = now
    req.resolved_by = resolved_by
    if staff_notes:
        req.staff_notes = staff_notes

    await db.commit()
    await db.refresh(req)

    logger.info(
        "Foster supply request fulfilled",
        extra={"supply_request_id": str(request_id), "resolved_by": str(resolved_by)},
    )
    return req


async def reject_request(
    db: AsyncSession,
    request_id: UUID,
    resolved_by: UUID,
    staff_notes: str | None = None,
) -> FosterSupplyRequest:
    """Reject a pending or approved supply request.

    Raises:
        ValueError: if not found or already fulfilled/rejected.
    """
    req = await _get_or_raise(db, request_id)

    if req.status == SupplyRequestStatus.FULFILLED:
        raise ValueError(f"Supply request {request_id} is already fulfilled and cannot be rejected")

    if req.status == SupplyRequestStatus.REJECTED:
        raise ValueError(f"Supply request {request_id} is already rejected")

    now = datetime.now(tz=UTC)
    req.status = SupplyRequestStatus.REJECTED
    req.resolved_at = now
    req.resolved_by = resolved_by
    if staff_notes:
        req.staff_notes = staff_notes

    await db.commit()
    await db.refresh(req)

    logger.info(
        "Foster supply request rejected",
        extra={"supply_request_id": str(request_id), "resolved_by": str(resolved_by)},
    )
    return req


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_or_raise(db: AsyncSession, request_id: UUID) -> FosterSupplyRequest:
    """Load a supply request by ID or raise ValueError with 'not found'."""
    result = await db.execute(
        select(FosterSupplyRequest).where(FosterSupplyRequest.id == request_id)
    )
    req: FosterSupplyRequest | None = result.scalar_one_or_none()
    if req is None:
        raise ValueError(f"Supply request {request_id} not found")
    return req
