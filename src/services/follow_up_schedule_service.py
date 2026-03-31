"""Service layer for post-adoption follow-up schedule management (RAP-261, EPIC-53).

Provides schedule visibility and maintenance:
- View upcoming follow-ups due within N days
- Detect and mark overdue follow-ups
- Per-adoption schedule summary

These functions complement the core follow_up_service (which handles creation,
surveys, and returns) with schedule-level analytics.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.follow_up import FollowUp, FollowUpStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DUE_WINDOW_DAYS = 7
"""Default lookahead window for 'due soon' queries (days)."""

MAX_DUE_WINDOW_DAYS = 90
"""Maximum lookahead window accepted by the API."""

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FollowUpScheduleItem:
    """Lightweight representation of a single scheduled follow-up."""

    id: UUID
    adoption_request_id: UUID
    scheduled_date: datetime
    day_offset: int
    status: str
    days_until_due: int
    is_overdue: bool


@dataclass(frozen=True)
class MarkOverdueResult:
    """Result of a bulk mark-overdue operation."""

    marked_count: int
    run_at: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_schedule_item(fu: FollowUp) -> FollowUpScheduleItem:
    now = datetime.now(UTC)
    scheduled = fu.scheduled_date
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=UTC)
    delta = (scheduled - now).days
    return FollowUpScheduleItem(
        id=fu.id,
        adoption_request_id=fu.adoption_request_id,
        scheduled_date=fu.scheduled_date,
        day_offset=fu.day_offset,
        status=fu.status,
        days_until_due=delta,
        is_overdue=delta < 0 and fu.status == FollowUpStatus.PENDING,
    )


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_due_follow_ups(
    db: AsyncSession,
    within_days: int = DEFAULT_DUE_WINDOW_DAYS,
) -> list[FollowUpScheduleItem]:
    """Return pending follow-ups scheduled within the next `within_days` days.

    Results are ordered by scheduled_date ascending (most urgent first).
    """
    now = datetime.now(UTC)
    cutoff = now + timedelta(days=within_days)

    result = await db.execute(
        select(FollowUp)
        .where(
            FollowUp.status == FollowUpStatus.PENDING,
            FollowUp.scheduled_date <= cutoff,
            FollowUp.scheduled_date >= now,
        )
        .order_by(FollowUp.scheduled_date)
    )
    return [_to_schedule_item(fu) for fu in result.scalars()]


async def get_overdue_follow_ups(db: AsyncSession) -> list[FollowUpScheduleItem]:
    """Return all pending follow-ups whose scheduled_date is in the past."""
    now = datetime.now(UTC)

    result = await db.execute(
        select(FollowUp)
        .where(
            FollowUp.status == FollowUpStatus.PENDING,
            FollowUp.scheduled_date < now,
        )
        .order_by(FollowUp.scheduled_date)
    )
    return [_to_schedule_item(fu) for fu in result.scalars()]


async def get_schedule_for_adoption(
    db: AsyncSession, adoption_request_id: UUID
) -> list[FollowUpScheduleItem]:
    """Return all follow-up schedule items for a specific adoption, ordered by day_offset."""
    result = await db.execute(
        select(FollowUp)
        .where(FollowUp.adoption_request_id == adoption_request_id)
        .order_by(FollowUp.day_offset)
    )
    return [_to_schedule_item(fu) for fu in result.scalars()]


async def mark_overdue_follow_ups(db: AsyncSession) -> MarkOverdueResult:
    """Bulk-update all past-due pending follow-ups to OVERDUE status.

    Idempotent: running multiple times has no additional effect.
    Returns the count of records updated.
    """
    now = datetime.now(UTC)

    result = await db.execute(
        update(FollowUp)
        .where(
            FollowUp.status == FollowUpStatus.PENDING,
            FollowUp.scheduled_date < now,
        )
        .values(
            status=FollowUpStatus.OVERDUE,
            updated_at=now,
        )
        .returning(FollowUp.id)
    )
    marked_ids = result.fetchall()
    marked_count = len(marked_ids)

    if marked_count > 0:
        logger.info("Marked %d follow-ups as overdue", marked_count)

    return MarkOverdueResult(
        marked_count=marked_count,
        run_at=now.isoformat(),
    )
