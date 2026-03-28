"""Voucher notification endpoints for donor transparency.

Endpoints:
    GET  /api/voucher-notifications          -- list donor's voucher notifications (paginated)
    GET  /api/voucher-notifications/{id}     -- get single notification detail
    POST /api/voucher-notifications/process  -- process pending notifications (admin)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.services.voucher_notification_service import (
    get_donor_notifications,
    get_pending_notifications,
    mark_notification_failed,
    mark_notification_sent,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/voucher-notifications",
    tags=["voucher-notifications"],
    responses=RESOURCE_RESPONSES,
)


# --- Schemas (co-located, small set) ---


class VoucherNotificationResponse(BaseModel):
    """Single voucher notification."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    event_type: str
    voucher_id: UUID | None = None
    channel: str
    status: str
    retry_count: int
    subject: str | None = None
    body_preview: str | None = None
    context_data: str | None = None
    created_at: str
    sent_at: str | None = None
    last_attempt_at: str | None = None


class VoucherNotificationListResponse(BaseModel):
    """Paginated list of voucher notifications."""

    items: list[VoucherNotificationResponse]
    total: int
    page: int
    page_size: int


class ProcessNotificationsResponse(BaseModel):
    """Result of processing pending notifications."""

    processed: int
    sent: int
    failed: int


# --- Endpoints ---


@router.get("", response_model=VoucherNotificationListResponse)
async def list_donor_voucher_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> VoucherNotificationListResponse:
    """List voucher notifications for the current donor (staff+)."""
    notifications, total = await get_donor_notifications(
        db,
        donor_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    return VoucherNotificationListResponse(
        items=[VoucherNotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/for-donor/{donor_id}", response_model=VoucherNotificationListResponse)
async def list_notifications_for_donor(
    donor_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> VoucherNotificationListResponse:
    """List voucher notifications for a specific donor (admin only)."""
    notifications, total = await get_donor_notifications(
        db,
        donor_id=donor_id,
        page=page,
        page_size=page_size,
    )
    return VoucherNotificationListResponse(
        items=[VoucherNotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/process",
    response_model=ProcessNotificationsResponse,
    status_code=status.HTTP_200_OK,
)
async def process_pending_notifications(
    limit: int = Query(50, ge=1, le=200, description="Max notifications to process"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> ProcessNotificationsResponse:
    """Process pending voucher notifications (admin only).

    Fetches pending notifications respecting rate limits, attempts delivery,
    and updates status accordingly. In production this would be called by
    a background worker; this endpoint enables manual triggering.
    """
    pending = await get_pending_notifications(db, limit=limit)

    sent_count = 0
    failed_count = 0

    for notification in pending:
        try:
            # Placeholder: actual delivery would happen here
            # (email via EmailService, WhatsApp via WhatsAppService)
            await mark_notification_sent(db, notification.id)
            sent_count += 1
        except Exception:
            logger.exception("Failed to deliver notification %s", notification.id)
            await mark_notification_failed(db, notification.id)
            failed_count += 1

    await db.commit()

    logger.info(
        "Processed %d notifications: %d sent, %d failed",
        len(pending),
        sent_count,
        failed_count,
    )

    return ProcessNotificationsResponse(
        processed=len(pending),
        sent=sent_count,
        failed=failed_count,
    )
