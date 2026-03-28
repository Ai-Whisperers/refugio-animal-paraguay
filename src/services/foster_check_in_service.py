"""Foster check-in schedule and reminder service (RAP-192).

Provides CRUD operations for foster check-in records and helpers for:
- Querying upcoming / overdue check-ins across all placements
- Marking a check-in as missed when its scheduled_at passes
- Logging reminder dispatch (actual delivery handled by notification layer)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.foster_check_in import (
    DEFAULT_INTERVAL_DAYS,
    CheckInStatus,
    CheckInType,
    FosterCheckIn,
)
from src.db.models.foster_placement import FosterPlacement

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UPCOMING_WINDOW_DAYS = 7  # how many days ahead counts as "upcoming"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def create_check_in(
    db: AsyncSession,
    *,
    placement_id: UUID,
    scheduled_at: datetime,
    check_in_type: CheckInType = CheckInType.SCHEDULED,
    interval_days: int = DEFAULT_INTERVAL_DAYS,
    created_by: UUID | None = None,
) -> FosterCheckIn:
    """Schedule a new check-in for an active foster placement.

    Raises ValueError if the placement does not exist or has already ended.
    """
    placement = await _get_active_placement_or_raise(db, placement_id)

    check_in = FosterCheckIn(
        foster_placement_id=placement.id,
        check_in_type=check_in_type.value,
        status=CheckInStatus.PENDING.value,
        scheduled_at=scheduled_at,
        interval_days=interval_days,
        created_by=created_by,
    )
    db.add(check_in)
    await db.commit()
    await db.refresh(check_in)
    logger.info(
        "Foster check-in scheduled",
        extra={
            "check_in_id": str(check_in.id),
            "placement_id": str(placement_id),
            "scheduled_at": scheduled_at.isoformat(),
        },
    )
    return check_in


async def list_check_ins_for_placement(
    db: AsyncSession,
    placement_id: UUID,
    *,
    status_filter: CheckInStatus | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[FosterCheckIn], int]:
    """Return paginated check-ins for a placement ordered by scheduled_at desc.

    Returns (items, total_count).
    """
    base_where = [FosterCheckIn.foster_placement_id == placement_id]
    if status_filter is not None:
        base_where.append(FosterCheckIn.status == status_filter.value)

    count_result = await db.execute(
        select(func.count()).select_from(FosterCheckIn).where(and_(*base_where))
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(FosterCheckIn)
        .where(and_(*base_where))
        .order_by(FosterCheckIn.scheduled_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def get_check_in_or_raise(db: AsyncSession, check_in_id: UUID) -> FosterCheckIn:
    """Return a check-in by ID or raise ValueError if not found."""
    result = await db.execute(select(FosterCheckIn).where(FosterCheckIn.id == check_in_id))
    check_in = result.scalar_one_or_none()
    if check_in is None:
        raise ValueError(f"Check-in {check_in_id} not found")
    return check_in


async def complete_check_in(
    db: AsyncSession,
    check_in_id: UUID,
    *,
    notes: str | None = None,
    auto_schedule_next: bool = True,
) -> FosterCheckIn:
    """Mark a pending check-in as completed.

    If auto_schedule_next is True and interval_days > 0, creates the next
    scheduled check-in automatically.

    Raises ValueError if check-in is not found or not in pending status.
    """
    check_in = await get_check_in_or_raise(db, check_in_id)

    if check_in.status != CheckInStatus.PENDING.value:
        raise ValueError(
            f"Cannot complete check-in with status '{check_in.status}'. "
            "Only pending check-ins can be completed."
        )

    now = datetime.now(UTC)
    check_in.status = CheckInStatus.COMPLETED.value
    check_in.completed_at = now
    check_in.notes = notes
    check_in.updated_at = now
    await db.flush()

    next_check_in: FosterCheckIn | None = None
    if auto_schedule_next and check_in.interval_days > 0:
        next_scheduled = now + timedelta(days=check_in.interval_days)
        next_check_in = FosterCheckIn(
            foster_placement_id=check_in.foster_placement_id,
            check_in_type=CheckInType.SCHEDULED.value,
            status=CheckInStatus.PENDING.value,
            scheduled_at=next_scheduled,
            interval_days=check_in.interval_days,
            created_by=check_in.created_by,
        )
        db.add(next_check_in)

    await db.commit()
    await db.refresh(check_in)
    logger.info(
        "Foster check-in completed",
        extra={
            "check_in_id": str(check_in_id),
            "auto_scheduled_next": next_check_in is not None,
        },
    )
    return check_in


async def cancel_check_in(
    db: AsyncSession,
    check_in_id: UUID,
    *,
    reason: str | None = None,
) -> FosterCheckIn:
    """Cancel a pending check-in.

    Raises ValueError if check-in is not found or not in pending status.
    """
    check_in = await get_check_in_or_raise(db, check_in_id)

    if check_in.status != CheckInStatus.PENDING.value:
        raise ValueError(
            f"Cannot cancel check-in with status '{check_in.status}'. "
            "Only pending check-ins can be cancelled."
        )

    now = datetime.now(UTC)
    check_in.status = CheckInStatus.CANCELLED.value
    check_in.cancellation_reason = reason
    check_in.updated_at = now
    await db.commit()
    await db.refresh(check_in)
    logger.info(
        "Foster check-in cancelled",
        extra={"check_in_id": str(check_in_id)},
    )
    return check_in


async def list_upcoming_check_ins(
    db: AsyncSession,
    *,
    days_ahead: int = UPCOMING_WINDOW_DAYS,
    include_overdue: bool = True,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[FosterCheckIn], int]:
    """Return pending check-ins due within the next `days_ahead` days.

    If include_overdue is True, also returns overdue check-ins (scheduled_at
    in the past with status still pending).

    Returns (items, total_count) ordered by scheduled_at ascending.
    """
    now = datetime.now(UTC)
    cutoff = now + timedelta(days=days_ahead)

    if include_overdue:
        scheduled_filter = FosterCheckIn.scheduled_at <= cutoff
    else:
        scheduled_filter = and_(
            FosterCheckIn.scheduled_at >= now,
            FosterCheckIn.scheduled_at <= cutoff,
        )

    base_where = and_(
        FosterCheckIn.status == CheckInStatus.PENDING.value,
        scheduled_filter,
    )

    count_result = await db.execute(
        select(func.count()).select_from(FosterCheckIn).where(base_where)
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(FosterCheckIn)
        .where(base_where)
        .order_by(FosterCheckIn.scheduled_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return items, total


async def mark_overdue_as_missed(db: AsyncSession) -> int:
    """Mark all pending check-ins past their scheduled_at as missed.

    Intended to be called by a periodic background task.
    Returns the number of records updated.
    """
    now = datetime.now(UTC)
    result = await db.execute(
        select(FosterCheckIn).where(
            and_(
                FosterCheckIn.status == CheckInStatus.PENDING.value,
                FosterCheckIn.scheduled_at < now,
            )
        )
    )
    overdue = list(result.scalars().all())
    for check_in in overdue:
        check_in.status = CheckInStatus.MISSED.value
        check_in.updated_at = now

    if overdue:
        await db.commit()
        logger.info("Marked %d foster check-ins as missed", len(overdue))
    return len(overdue)


async def record_reminder_sent(
    db: AsyncSession,
    check_in_id: UUID,
) -> FosterCheckIn:
    """Record that a reminder notification was dispatched for this check-in.

    Does not actually send any notification — that is handled by the
    notification service layer.  This function only updates the timestamp.
    """
    check_in = await get_check_in_or_raise(db, check_in_id)
    now = datetime.now(UTC)
    check_in.reminder_sent_at = now
    check_in.updated_at = now
    await db.commit()
    await db.refresh(check_in)
    logger.info(
        "Foster check-in reminder recorded",
        extra={"check_in_id": str(check_in_id)},
    )
    return check_in


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_active_placement_or_raise(db: AsyncSession, placement_id: UUID) -> FosterPlacement:
    """Return an active (not ended) foster placement or raise ValueError."""
    result = await db.execute(
        select(FosterPlacement).where(
            and_(
                FosterPlacement.id == placement_id,
                FosterPlacement.ended_at.is_(None),
            )
        )
    )
    placement = result.scalar_one_or_none()
    if placement is None:
        raise ValueError(
            f"Active foster placement {placement_id} not found. "
            "The placement may not exist or may have already ended."
        )
    return placement
