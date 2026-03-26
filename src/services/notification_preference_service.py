"""Notification preference service.

Manages per-user, per-type, per-channel notification preferences.
Missing preferences are treated as enabled (opt-out model: users
explicitly disable what they don't want).

Functions:
    get_preferences       -- list all preferences for a user
    update_preferences    -- bulk upsert preferences
    is_notification_enabled -- check if a specific notification is enabled
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.notification_preference import (
    NotificationChannel,
    NotificationPreference,
)

logger = logging.getLogger(__name__)

# All known notification types — must match CHECK constraint
NOTIFICATION_TYPES = [
    "adoption_request_created",
    "adoption_status_changed",
    "donation_received",
    "donation_refunded",
    "animal_intake_completed",
    "animal_status_changed",
    "system_alert",
    "gdpr_request",
]

CHANNELS = [NotificationChannel.IN_APP, NotificationChannel.EMAIL]


async def get_preferences(
    db: AsyncSession,
    user_id: UUID,
) -> list[NotificationPreference]:
    """Get all notification preferences for a user.

    Returns existing preference rows. Missing combinations are implicitly
    enabled (the UI should fill in defaults client-side).

    Args:
        db: Async database session.
        user_id: Owner of the preferences.

    Returns:
        List of NotificationPreference instances.
    """
    stmt = (
        sa.select(NotificationPreference)
        .where(NotificationPreference.user_id == user_id)
        .order_by(
            NotificationPreference.notification_type,
            NotificationPreference.channel,
        )
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_preferences_with_defaults(
    db: AsyncSession,
    user_id: UUID,
) -> list[dict]:
    """Get all preferences with defaults filled in for missing combinations.

    Returns a complete matrix of notification_type x channel, with
    explicit preferences taking priority and missing ones defaulting
    to enabled=True.

    Args:
        db: Async database session.
        user_id: Owner of the preferences.

    Returns:
        List of dicts with notification_type, channel, enabled keys.
    """
    existing = await get_preferences(db, user_id)
    existing_map = {(p.notification_type, p.channel): p.enabled for p in existing}

    result = []
    for ntype in NOTIFICATION_TYPES:
        for channel in CHANNELS:
            enabled = existing_map.get((ntype, channel), True)
            result.append(
                {
                    "notification_type": ntype,
                    "channel": channel,
                    "enabled": enabled,
                }
            )
    return result


async def update_preferences(
    db: AsyncSession,
    user_id: UUID,
    updates: list[dict],
) -> list[NotificationPreference]:
    """Bulk upsert notification preferences.

    Each update dict must have: notification_type, channel, enabled.
    Existing rows are updated; missing rows are inserted.

    Args:
        db: Async database session.
        user_id: Owner of the preferences.
        updates: List of preference dicts to upsert.

    Returns:
        List of updated/created NotificationPreference instances.
    """
    results = []
    now = datetime.now(UTC)

    for update in updates:
        ntype = update["notification_type"]
        channel = update["channel"]
        enabled = update["enabled"]

        # Try to find existing preference
        stmt = sa.select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == ntype,
            NotificationPreference.channel == channel,
        )
        result = await db.execute(stmt)
        pref = result.scalar_one_or_none()

        if pref is not None:
            pref.enabled = enabled
            pref.updated_at = now
        else:
            pref = NotificationPreference(
                user_id=user_id,
                notification_type=ntype,
                channel=channel,
                enabled=enabled,
                updated_at=now,
            )
            db.add(pref)

        await db.flush()
        results.append(pref)

    logger.info(
        "Updated %d notification preferences for user_id=%s",
        len(results),
        user_id,
    )
    return results


async def is_notification_enabled(
    db: AsyncSession,
    user_id: UUID,
    notification_type: str,
    channel: str,
) -> bool:
    """Check if a specific notification type+channel is enabled for a user.

    Missing preferences are treated as enabled (opt-out model).

    Args:
        db: Async database session.
        user_id: Target user.
        notification_type: The notification category.
        channel: The delivery channel (in_app, email).

    Returns:
        True if the notification should be sent, False if opted out.
    """
    stmt = sa.select(NotificationPreference.enabled).where(
        NotificationPreference.user_id == user_id,
        NotificationPreference.notification_type == notification_type,
        NotificationPreference.channel == channel,
    )
    result = await db.execute(stmt)
    enabled = result.scalar_one_or_none()

    # Missing preference = enabled (opt-out model)
    if enabled is None:
        return True
    return enabled
