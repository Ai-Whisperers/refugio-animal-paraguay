"""Service for sending shift reminder notifications to volunteers.

Finds volunteers with upcoming shifts who have not yet received a reminder,
creates an in-app notification for each, and stamps reminder_sent_at to
prevent duplicate sends.

Functions:
    send_shift_reminders  -- batch-send reminders for shifts within a time window
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.notification import NotificationType
from src.db.models.shift import Shift, ShiftSignup, ShiftStatus
from src.services.notification_service import create_notification

logger = logging.getLogger(__name__)

DEFAULT_HOURS_AHEAD = 24
DEFAULT_BATCH_SIZE = 100

# Statuses that should NOT receive reminders
REMINDER_EXCLUDED_STATUSES = {ShiftStatus.CANCELLED.value, ShiftStatus.COMPLETED.value}


async def send_shift_reminders(
    db: AsyncSession,
    *,
    hours_ahead: int = DEFAULT_HOURS_AHEAD,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    """Send in-app reminder notifications to volunteers with upcoming shifts.

    Finds all shift signups where:
    - reminder_sent_at IS NULL (not yet reminded)
    - The associated shift falls within the next ``hours_ahead`` hours
    - The shift is not cancelled or completed

    Creates one in-app notification per signup and stamps reminder_sent_at
    to prevent duplicate sends on subsequent calls.

    Args:
        db: Async database session.
        hours_ahead: Look-ahead window in hours. Default 24.
        batch_size: Maximum number of reminders to send per call.

    Returns:
        dict with keys: sent_count, hours_ahead, sent_at
    """
    now = datetime.now(UTC)
    window_end_date: date = (now + timedelta(hours=hours_ahead)).date()
    today: date = now.date()

    stmt = (
        select(ShiftSignup, Shift)
        .join(Shift, ShiftSignup.shift_id == Shift.id)
        .where(
            ShiftSignup.reminder_sent_at.is_(None),
            Shift.shift_date >= today,
            Shift.shift_date <= window_end_date,
            Shift.status.not_in(list(REMINDER_EXCLUDED_STATUSES)),
        )
        .order_by(Shift.shift_date, Shift.start_time)
        .limit(batch_size)
    )

    result = await db.execute(stmt)
    rows = result.all()

    sent_count = 0
    for signup, shift in rows:
        shift_date_str = shift.shift_date.strftime("%d/%m/%Y")
        start_time_str = str(shift.start_time)[:5]  # HH:MM
        title = "Recordatorio de turno"
        message = (
            f"Tienes un turno el {shift_date_str} a las {start_time_str}. "
            "¡Te esperamos en el Refugio Animal Paraguay!"
        )
        if shift.title:
            message = f"Turno: {shift.title}. " + message

        await create_notification(
            db,
            user_id=signup.volunteer_id,
            notification_type=NotificationType.VOLUNTEER_SHIFT_REMINDER,
            title=title,
            message=message,
            data={
                "shift_id": str(shift.id),
                "shift_date": shift_date_str,
                "start_time": start_time_str,
                "role": shift.role,
            },
        )
        signup.reminder_sent_at = now
        sent_count += 1

    if sent_count > 0:
        await db.commit()

    logger.info(
        "Shift reminders sent",
        extra={"sent_count": sent_count, "hours_ahead": hours_ahead},
    )
    return {
        "sent_count": sent_count,
        "hours_ahead": hours_ahead,
        "sent_at": now,
    }
