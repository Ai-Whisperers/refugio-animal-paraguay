"""API endpoints for follow-up automation.

Extends the existing follow-up system with automation endpoints:
batch processing, reminders, skip, alerts, and completion stats.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_db
from src.services.followup_automation_service import (
    FollowUpNotFoundError,
    InvalidFollowUpStateError,
    check_for_alerts,
    get_followup_completion_stats,
    process_due_followups,
    send_followup_reminders,
    skip_followup,
)

admin_router = APIRouter(tags=["Follow-Up Automation"])
public_router = APIRouter(tags=["Follow-Up Automation"])


# --- Schemas ---


class BatchProcessResponse(BaseModel):
    """Response from batch follow-up processing."""

    processed_count: int
    batch_size: int
    processed_at: datetime

    model_config = {"from_attributes": True}


class ReminderResponse(BaseModel):
    """Response from reminder processing."""

    reminder_count: int
    grace_days: int
    processed_at: datetime

    model_config = {"from_attributes": True}


class SkipResponse(BaseModel):
    """Response after skipping a follow-up."""

    follow_up_id: UUID
    status: str
    skipped_at: datetime

    model_config = {"from_attributes": True}


class AlertItem(BaseModel):
    """A follow-up that needs staff attention."""

    follow_up_id: UUID
    adoption_request_id: UUID
    welfare_score: int | None = None
    satisfaction_score: int | None = None
    issues_noted: str | None = None
    day_offset: int
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class CompletionStatsResponse(BaseModel):
    """Follow-up completion statistics."""

    total_followups: int
    completed: int
    overdue: int
    pending: int
    sent: int
    completion_pct: float
    adoption_request_id: UUID | None = None

    model_config = {"from_attributes": True}


# --- Admin endpoints ---


@admin_router.post(
    "/api/admin/follow-ups/process-due",
    response_model=BatchProcessResponse,
)
async def process_due_followups_endpoint(
    batch_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Process pending follow-ups whose scheduled date has passed.

    Marks them as 'sent' (simulates notification dispatch).
    Intended to be called by a scheduled job (Celery Beat).
    """
    result = await process_due_followups(db, batch_size=batch_size)
    await db.commit()
    return result


@admin_router.post(
    "/api/admin/follow-ups/send-reminders",
    response_model=ReminderResponse,
)
async def send_reminders_endpoint(
    batch_size: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Send reminders for follow-ups not completed within grace period.

    Marks overdue follow-ups and would trigger reminder notifications.
    """
    result = await send_followup_reminders(db, batch_size=batch_size)
    await db.commit()
    return result


@admin_router.get(
    "/api/admin/follow-ups/alerts",
    response_model=list[AlertItem],
)
async def get_followup_alerts(
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> list[dict]:
    """Get follow-ups that need staff attention (low welfare, reported issues)."""
    return await check_for_alerts(db)


@admin_router.get(
    "/api/admin/follow-ups/completion-stats",
    response_model=CompletionStatsResponse,
)
async def get_completion_stats(
    adoption_request_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> dict:
    """Get follow-up completion statistics, optionally for a specific adoption."""
    return await get_followup_completion_stats(db, adoption_request_id)


# --- Public endpoint (adopter-facing) ---


@public_router.post(
    "/api/follow-ups/{follow_up_id}/skip",
    response_model=SkipResponse,
)
async def skip_followup_endpoint(
    follow_up_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Allow an adopter to skip a follow-up (prefer not to respond)."""
    try:
        result = await skip_followup(db, follow_up_id)
        await db.commit()
        return result
    except FollowUpNotFoundError:
        raise HTTPException(status_code=404, detail="Follow-up not found") from None
    except InvalidFollowUpStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
