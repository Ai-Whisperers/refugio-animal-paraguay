"""Notification channel frequency service.

Manages per-user, per-channel notification delivery frequency settings.
Controls whether notifications are delivered immediately or batched into
daily/weekly digest emails.

Functions:
    get_channel_frequencies  -- get all frequency settings for a user
    set_channel_frequency    -- upsert frequency for one channel
    get_frequency            -- get frequency for a specific channel
    is_immediate             -- check if a channel uses immediate delivery
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.notification_channel_frequency import (
    NotificationChannelFrequency,
    NotificationFrequency,
)

logger = logging.getLogger(__name__)

SUPPORTED_CHANNELS = ["in_app", "email"]

DEFAULT_FREQUENCY = NotificationFrequency.IMMEDIATE


async def get_channel_frequencies(
    db: AsyncSession,
    user_id: UUID,
) -> list[dict]:
    """Get all channel frequency settings for a user with defaults.

    Missing channels default to IMMEDIATE. Returns entries for all
    supported channels.

    Args:
        db: Async database session.
        user_id: Owner of the frequency settings.

    Returns:
        List of dicts with channel and frequency keys.
    """
    stmt = (
        sa.select(NotificationChannelFrequency)
        .where(NotificationChannelFrequency.user_id == user_id)
        .order_by(NotificationChannelFrequency.channel)
    )
    result = await db.execute(stmt)
    existing = list(result.scalars().all())
    existing_map = {row.channel: row.frequency for row in existing}

    return [
        {
            "channel": channel,
            "frequency": existing_map.get(channel, DEFAULT_FREQUENCY),
        }
        for channel in SUPPORTED_CHANNELS
    ]


async def set_channel_frequency(
    db: AsyncSession,
    user_id: UUID,
    channel: str,
    frequency: str,
) -> NotificationChannelFrequency:
    """Upsert frequency setting for one channel.

    Creates a new row if none exists, updates existing row otherwise.

    Args:
        db: Async database session.
        user_id: Owner of the frequency setting.
        channel: Delivery channel (in_app, email).
        frequency: Desired frequency (immediate, daily_digest, weekly).

    Returns:
        The updated or created NotificationChannelFrequency instance.
    """
    stmt = sa.select(NotificationChannelFrequency).where(
        NotificationChannelFrequency.user_id == user_id,
        NotificationChannelFrequency.channel == channel,
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    now = datetime.now(UTC)
    if row is not None:
        row.frequency = frequency
        row.updated_at = now
    else:
        row = NotificationChannelFrequency(
            user_id=user_id,
            channel=channel,
            frequency=frequency,
            updated_at=now,
        )
        db.add(row)

    await db.flush()
    logger.info(
        "Set notification frequency channel=%s frequency=%s for user_id=%s",
        channel,
        frequency,
        user_id,
    )
    return row


async def get_frequency(
    db: AsyncSession,
    user_id: UUID,
    channel: str,
) -> str:
    """Get delivery frequency for a specific channel.

    Missing setting defaults to IMMEDIATE.

    Args:
        db: Async database session.
        user_id: Target user.
        channel: Delivery channel.

    Returns:
        The frequency string (immediate, daily_digest, weekly).
    """
    stmt = sa.select(NotificationChannelFrequency.frequency).where(
        NotificationChannelFrequency.user_id == user_id,
        NotificationChannelFrequency.channel == channel,
    )
    result = await db.execute(stmt)
    freq = result.scalar_one_or_none()
    return freq if freq is not None else DEFAULT_FREQUENCY


async def is_immediate(
    db: AsyncSession,
    user_id: UUID,
    channel: str,
) -> bool:
    """Check if a channel uses immediate delivery for a user.

    Used by notification routing logic to decide whether to send
    immediately or queue for digest processing.

    Args:
        db: Async database session.
        user_id: Target user.
        channel: Delivery channel.

    Returns:
        True if the channel should deliver immediately, False if batched.
    """
    freq = await get_frequency(db, user_id, channel)
    return freq == NotificationFrequency.IMMEDIATE
