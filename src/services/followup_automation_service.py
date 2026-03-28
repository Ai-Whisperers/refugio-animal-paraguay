"""Service layer for post-adoption follow-up automation.

Handles scheduled processing of due follow-ups, sending reminders,
detecting overdue items, skipping follow-ups, alerting on issues,
and calculating follow-up completion metrics.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.follow_up import FollowUp, FollowUpStatus

logger = logging.getLogger(__name__)

# Follow-up reminders are sent this many days after the scheduled date
REMINDER_GRACE_DAYS = 3

# Welfare score at or below this triggers a staff alert
ALERT_WELFARE_THRESHOLD = 2

# Maximum number of follow-ups to process per batch
DEFAULT_BATCH_SIZE = 100

# Skipped status constant
STATUS_SKIPPED = "skipped"


class FollowUpAutomationError(Exception):
    """Base error for follow-up automation operations."""


class FollowUpNotFoundError(FollowUpAutomationError):
    """Raised when a follow-up record does not exist."""


class InvalidFollowUpStateError(FollowUpAutomationError):
    """Raised when a follow-up is in a state that prevents the operation."""


async def process_due_followups(
    db: AsyncSession,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    """Find pending follow-ups whose scheduled_date has passed and mark them sent.

    This simulates sending notifications (email/WhatsApp) for due follow-ups.
    In production, each would trigger an actual notification.

    Returns counts of processed and already-overdue items.
    """
    now = datetime.now(UTC)

    # Find pending follow-ups that are due (scheduled_date <= now)
    result = await db.execute(
        select(FollowUp)
        .where(
            FollowUp.status == FollowUpStatus.PENDING.value,
            FollowUp.scheduled_date <= now,
        )
        .order_by(FollowUp.scheduled_date.asc())
        .limit(batch_size)
    )
    due_followups = list(result.scalars().all())

    sent_count = 0
    for fu in due_followups:
        fu.status = FollowUpStatus.SENT.value
        fu.survey_sent_at = now
        sent_count += 1

    if sent_count > 0:
        await db.flush()

    logger.info("Processed %d due follow-ups", sent_count)

    return {
        "processed_count": sent_count,
        "batch_size": batch_size,
        "processed_at": now,
    }


async def send_followup_reminders(
    db: AsyncSession,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    """Find sent follow-ups that have not been completed after REMINDER_GRACE_DAYS.

    Marks them as overdue and would trigger a reminder notification.
    """
    now = datetime.now(UTC)
    reminder_cutoff = now - timedelta(days=REMINDER_GRACE_DAYS)

    result = await db.execute(
        select(FollowUp)
        .where(
            FollowUp.status == FollowUpStatus.SENT.value,
            FollowUp.survey_sent_at.isnot(None),
            FollowUp.survey_sent_at <= reminder_cutoff,
        )
        .order_by(FollowUp.survey_sent_at.asc())
        .limit(batch_size)
    )
    overdue_followups = list(result.scalars().all())

    overdue_count = 0
    for fu in overdue_followups:
        fu.status = FollowUpStatus.OVERDUE.value
        overdue_count += 1

    if overdue_count > 0:
        await db.flush()

    logger.info("Marked %d follow-ups as overdue (reminder sent)", overdue_count)

    return {
        "reminder_count": overdue_count,
        "grace_days": REMINDER_GRACE_DAYS,
        "processed_at": now,
    }


async def skip_followup(
    db: AsyncSession,
    follow_up_id: UUID,
) -> dict:
    """Allow an adopter to skip a follow-up (prefer not to respond).

    Raises FollowUpNotFoundError if not found.
    Raises InvalidFollowUpStateError if already completed or cancelled.
    """
    fu = await db.get(FollowUp, follow_up_id)
    if fu is None:
        raise FollowUpNotFoundError(f"Follow-up {follow_up_id} not found")

    terminal_statuses = {
        FollowUpStatus.COMPLETED.value,
        FollowUpStatus.CANCELLED.value,
        STATUS_SKIPPED,
    }
    if fu.status in terminal_statuses:
        raise InvalidFollowUpStateError(f"Follow-up already in terminal state: {fu.status}")

    now = datetime.now(UTC)
    fu.status = STATUS_SKIPPED
    fu.updated_at = now

    await db.flush()

    logger.info("Follow-up %s skipped by adopter", follow_up_id)

    return {
        "follow_up_id": fu.id,
        "status": STATUS_SKIPPED,
        "skipped_at": now,
    }


async def check_for_alerts(
    db: AsyncSession,
) -> list[dict]:
    """Find completed follow-ups with low welfare scores or reported issues.

    Returns a list of follow-ups that need staff attention.
    """
    result = await db.execute(
        select(FollowUp)
        .where(
            FollowUp.status == FollowUpStatus.COMPLETED.value,
            (
                (FollowUp.welfare_score.isnot(None))
                & (FollowUp.welfare_score <= ALERT_WELFARE_THRESHOLD)
            )
            | (FollowUp.issues_noted.isnot(None)),
        )
        .order_by(FollowUp.survey_completed_at.desc())
    )
    flagged = result.scalars().all()

    return [
        {
            "follow_up_id": fu.id,
            "adoption_request_id": fu.adoption_request_id,
            "welfare_score": fu.welfare_score,
            "satisfaction_score": fu.satisfaction_score,
            "issues_noted": fu.issues_noted,
            "day_offset": fu.day_offset,
            "completed_at": fu.survey_completed_at,
        }
        for fu in flagged
    ]


async def get_followup_completion_stats(
    db: AsyncSession,
    adoption_request_id: UUID | None = None,
) -> dict:
    """Calculate follow-up completion percentage.

    If adoption_request_id is provided, returns stats for that adoption only.
    Otherwise returns global stats.
    """
    base_query = select(
        func.count().label("total"),
        func.count()
        .filter(
            FollowUp.status.in_(
                [
                    FollowUpStatus.COMPLETED.value,
                    STATUS_SKIPPED,
                ]
            )
        )
        .label("completed"),
        func.count().filter(FollowUp.status == FollowUpStatus.OVERDUE.value).label("overdue"),
        func.count().filter(FollowUp.status == FollowUpStatus.PENDING.value).label("pending"),
        func.count().filter(FollowUp.status == FollowUpStatus.SENT.value).label("sent"),
    ).select_from(FollowUp)

    if adoption_request_id is not None:
        base_query = base_query.where(FollowUp.adoption_request_id == adoption_request_id)

    result = await db.execute(base_query)
    row = result.one()

    total = row.total
    completed = row.completed
    completion_pct = round(completed / total * 100, 1) if total > 0 else 0.0

    return {
        "total_followups": total,
        "completed": completed,
        "overdue": row.overdue,
        "pending": row.pending,
        "sent": row.sent,
        "completion_pct": completion_pct,
        "adoption_request_id": adoption_request_id,
    }
