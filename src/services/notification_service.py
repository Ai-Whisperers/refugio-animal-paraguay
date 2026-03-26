"""In-app notification service.

Provides CRUD operations for persistent in-app notifications. Notifications
are created by event bus handlers or direct service calls and queried by
the notifications API.

Functions:
    create_notification  -- create a new notification for a user
    list_notifications   -- list notifications with pagination and read filter
    get_unread_count     -- count unread notifications for a user
    mark_read            -- mark a single notification as read
    mark_all_read        -- mark all notifications as read for a user
    delete_notification  -- hard-delete a single notification
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.notification import Notification

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


async def create_notification(
    db: AsyncSession,
    *,
    user_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    data: dict | None = None,
) -> Notification:
    """Create and persist a new notification.

    Args:
        db: Async database session.
        user_id: Target user who will see the notification.
        notification_type: One of NotificationType values.
        title: Short headline for the notification.
        message: Full notification body text.
        data: Optional JSON payload with event-specific context.

    Returns:
        The newly created Notification instance.
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        data=data,
    )
    db.add(notification)
    await db.flush()
    logger.info(
        "Created notification type=%s for user_id=%s",
        notification_type,
        user_id,
    )
    return notification


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    *,
    is_read: bool | None = None,
    offset: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> list[Notification]:
    """List notifications for a user with optional read-status filter.

    Args:
        db: Async database session.
        user_id: Owner of the notifications.
        is_read: If set, filter by read status. None returns all.
        offset: Pagination offset.
        limit: Page size (capped at MAX_PAGE_SIZE).

    Returns:
        List of Notification instances ordered by created_at DESC.
    """
    effective_limit = min(limit, MAX_PAGE_SIZE)
    stmt = (
        sa.select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(effective_limit)
    )
    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_unread_count(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Count unread notifications for a user.

    Args:
        db: Async database session.
        user_id: Owner of the notifications.

    Returns:
        Number of unread notifications.
    """
    stmt = (
        sa.select(sa.func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == sa.false())
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def mark_read(
    db: AsyncSession,
    notification_id: UUID,
    user_id: UUID,
) -> Notification | None:
    """Mark a single notification as read.

    Args:
        db: Async database session.
        notification_id: ID of the notification to mark.
        user_id: Owner of the notification (prevents cross-user access).

    Returns:
        Updated Notification if found and owned by user, else None.
    """
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        return None

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await db.flush()

    return notification


async def mark_all_read(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Mark all unread notifications as read for a user.

    Args:
        db: Async database session.
        user_id: Owner of the notifications.

    Returns:
        Number of notifications marked as read.
    """
    now = datetime.now(UTC)
    stmt = (
        sa.update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == sa.false())
        .values(is_read=True, read_at=now)
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount  # type: ignore[return-value]


async def delete_notification(
    db: AsyncSession,
    notification_id: UUID,
    user_id: UUID,
) -> bool:
    """Delete a single notification.

    Args:
        db: Async database session.
        notification_id: ID of the notification to delete.
        user_id: Owner of the notification (prevents cross-user access).

    Returns:
        True if deleted, False if not found or not owned by user.
    """
    notification = await db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        return False

    await db.delete(notification)
    await db.flush()
    return True
