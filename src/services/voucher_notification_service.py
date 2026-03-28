"""Service for voucher donor transparency notifications.

Creates, queues, and manages notification events for voucher lifecycle
transitions (claimed, redeemed) and monthly donor summaries.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.voucher_notification import (
    MAX_RETRY_COUNT,
    NotificationChannel,
    NotificationStatus,
    VoucherNotification,
    VoucherNotificationType,
)

logger = logging.getLogger(__name__)

# Rate limit: minimum interval between notifications to same user
RATE_LIMIT_MINUTES = 60


class NotificationNotFoundError(Exception):
    """Raised when a notification record is not found."""

    def __init__(self, notification_id: UUID) -> None:
        self.notification_id = notification_id
        self.message = f"Notification {notification_id} not found."
        super().__init__(self.message)


async def create_voucher_claimed_notification(
    db: AsyncSession,
    *,
    donor_id: UUID,
    voucher_id: UUID,
    rescuer_name: str,
    clinic_name: str,
    service_type: str,
    animal_name: str | None = None,
    channel: str = NotificationChannel.EMAIL,
) -> VoucherNotification:
    """Create a notification for when a rescuer claims a voucher."""
    context = {
        "rescuer_name": rescuer_name,
        "clinic_name": clinic_name,
        "service_type": service_type,
        "animal_name": animal_name or "an animal in need",
    }

    subject = "Your voucher has been claimed!"
    body_preview = (
        f"A rescuer has claimed your {service_type} voucher "
        f"at {clinic_name} for {context['animal_name']}."
    )

    notification = VoucherNotification(
        user_id=donor_id,
        event_type=VoucherNotificationType.VOUCHER_CLAIMED,
        voucher_id=voucher_id,
        channel=channel,
        status=NotificationStatus.PENDING,
        subject=subject,
        body_preview=body_preview,
        context_data=json.dumps(context),
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)

    logger.info(
        "Created voucher_claimed notification for donor %s (voucher=%s)",
        donor_id,
        voucher_id,
    )
    return notification


async def create_voucher_redeemed_notification(
    db: AsyncSession,
    *,
    donor_id: UUID,
    voucher_id: UUID,
    clinic_name: str,
    service_type: str,
    animal_name: str | None = None,
    proof_description: str | None = None,
    channel: str = NotificationChannel.EMAIL,
) -> VoucherNotification:
    """Create a notification for when a clinic redeems a voucher."""
    context = {
        "clinic_name": clinic_name,
        "service_type": service_type,
        "animal_name": animal_name or "an animal in need",
        "proof_description": proof_description,
    }

    subject = "Your voucher helped an animal!"
    body_preview = (
        f"Your {service_type} voucher was redeemed at {clinic_name} "
        f"for {context['animal_name']}."
    )

    notification = VoucherNotification(
        user_id=donor_id,
        event_type=VoucherNotificationType.VOUCHER_REDEEMED,
        voucher_id=voucher_id,
        channel=channel,
        status=NotificationStatus.PENDING,
        subject=subject,
        body_preview=body_preview,
        context_data=json.dumps(context),
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)

    logger.info(
        "Created voucher_redeemed notification for donor %s (voucher=%s)",
        donor_id,
        voucher_id,
    )
    return notification


async def create_monthly_summary_notification(
    db: AsyncSession,
    *,
    donor_id: UUID,
    month: int,
    year: int,
    total_purchased: int,
    total_redeemed: int,
    total_claimed: int,
    animals_helped: int,
    total_amount_eur: float | None = None,
    channel: str = NotificationChannel.EMAIL,
) -> VoucherNotification:
    """Create a monthly summary notification for a donor."""
    context = {
        "month": month,
        "year": year,
        "total_purchased": total_purchased,
        "total_redeemed": total_redeemed,
        "total_claimed": total_claimed,
        "animals_helped": animals_helped,
        "total_amount_eur": total_amount_eur,
    }

    subject = f"Your monthly voucher impact summary - {month}/{year}"
    body_preview = (
        f"In {month}/{year}: {total_purchased} purchased, "
        f"{total_redeemed} redeemed, {animals_helped} animals helped."
    )

    notification = VoucherNotification(
        user_id=donor_id,
        event_type=VoucherNotificationType.MONTHLY_SUMMARY,
        voucher_id=None,
        channel=channel,
        status=NotificationStatus.PENDING,
        subject=subject,
        body_preview=body_preview,
        context_data=json.dumps(context),
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)

    logger.info(
        "Created monthly_summary notification for donor %s (%d/%d)",
        donor_id,
        month,
        year,
    )
    return notification


async def get_pending_notifications(
    db: AsyncSession,
    *,
    limit: int = 50,
) -> list[VoucherNotification]:
    """Fetch pending notifications ready for delivery.

    Respects rate limiting: skips users who received a notification
    within the last RATE_LIMIT_MINUTES.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=RATE_LIMIT_MINUTES)

    # Subquery: users who received a notification recently
    recent_recipients = (
        select(VoucherNotification.user_id)
        .where(
            VoucherNotification.sent_at > cutoff,
            VoucherNotification.status == NotificationStatus.SENT,
        )
        .distinct()
    )

    query = (
        select(VoucherNotification)
        .where(
            VoucherNotification.status == NotificationStatus.PENDING,
            VoucherNotification.retry_count < MAX_RETRY_COUNT,
            VoucherNotification.user_id.not_in(recent_recipients),
        )
        .order_by(VoucherNotification.created_at)
        .limit(limit)
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def mark_notification_sent(
    db: AsyncSession,
    notification_id: UUID,
) -> None:
    """Mark a notification as successfully sent."""
    now = datetime.now(UTC)
    stmt = (
        update(VoucherNotification)
        .where(VoucherNotification.id == notification_id)
        .values(
            status=NotificationStatus.SENT,
            sent_at=now,
            last_attempt_at=now,
        )
    )
    await db.execute(stmt)
    await db.flush()


async def mark_notification_failed(
    db: AsyncSession,
    notification_id: UUID,
) -> None:
    """Increment retry count and mark as failed if max retries exceeded."""
    now = datetime.now(UTC)

    # Fetch current retry count
    result = await db.execute(
        select(VoucherNotification.retry_count).where(VoucherNotification.id == notification_id)
    )
    row = result.one_or_none()
    if row is None:
        raise NotificationNotFoundError(notification_id)

    new_retry = row.retry_count + 1
    new_status = (
        NotificationStatus.FAILED if new_retry >= MAX_RETRY_COUNT else NotificationStatus.PENDING
    )

    stmt = (
        update(VoucherNotification)
        .where(VoucherNotification.id == notification_id)
        .values(
            retry_count=new_retry,
            status=new_status,
            last_attempt_at=now,
        )
    )
    await db.execute(stmt)
    await db.flush()

    if new_status == NotificationStatus.FAILED:
        logger.warning(
            "Notification %s permanently failed after %d attempts",
            notification_id,
            new_retry,
        )


async def get_donor_notifications(
    db: AsyncSession,
    donor_id: UUID,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[VoucherNotification], int]:
    """List notifications for a donor (most recent first)."""
    query = (
        select(VoucherNotification)
        .where(VoucherNotification.user_id == donor_id)
        .order_by(VoucherNotification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    count_query = select(func.count(VoucherNotification.id)).where(
        VoucherNotification.user_id == donor_id
    )

    result = await db.execute(query)
    notifications = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return notifications, total
