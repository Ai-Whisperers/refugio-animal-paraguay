"""Shift reminder notification API (RAP-184).

Staff-triggered batch endpoint that sends in-app shift reminder notifications
to volunteers with upcoming shifts.

Endpoints:
    POST /api/shifts/reminders/send  -- send reminders for upcoming shifts (staff only)
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_db
from src.services.shift_reminder_service import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_HOURS_AHEAD,
    send_shift_reminders,
)

router = APIRouter(tags=["Shifts"])

MAX_HOURS_AHEAD = 168  # 1 week


class ShiftReminderResponse(BaseModel):
    """Response from a shift reminder batch run."""

    sent_count: int
    hours_ahead: int
    sent_at: datetime


@router.post("/api/shifts/reminders/send", response_model=ShiftReminderResponse)
async def send_shift_reminder_notifications(
    hours_ahead: int = Query(
        DEFAULT_HOURS_AHEAD,
        ge=1,
        le=MAX_HOURS_AHEAD,
        description="Look-ahead window in hours (default 24, max 168)",
    ),
    batch_size: int = Query(
        DEFAULT_BATCH_SIZE,
        ge=1,
        le=500,
        description="Maximum number of reminders to send",
    ),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> ShiftReminderResponse:
    """Send in-app shift reminders to volunteers with upcoming shifts.

    Idempotent: only signups without a prior reminder are processed.
    Cancelled and completed shifts are excluded.
    """
    result = await send_shift_reminders(db, hours_ahead=hours_ahead, batch_size=batch_size)
    return ShiftReminderResponse(**result)
