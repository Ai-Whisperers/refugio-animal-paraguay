"""SQLAlchemy ORM model for per-channel notification frequency settings.

Stores the delivery frequency preference per user per channel.
The frequency controls how often email notifications are batched
and sent (immediately, once per day, or once per week).
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class NotificationFrequency(enum.StrEnum):
    """Delivery frequency for batched notifications."""

    IMMEDIATE = "immediate"
    DAILY_DIGEST = "daily_digest"
    WEEKLY = "weekly"


class NotificationChannelFrequency(Base):
    """Per-user notification frequency for a specific delivery channel.

    Each row represents the desired delivery cadence for a channel.
    Missing rows default to IMMEDIATE (opt-in model for batching).
    Only the 'email' channel benefits from batching; 'in_app'
    notifications are always delivered immediately.
    """

    __tablename__ = "notification_channel_frequency"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
    )
    frequency: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=NotificationFrequency.IMMEDIATE,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "user_id",
            "channel",
            name="uq_notification_channel_frequency_user_channel",
        ),
        sa.CheckConstraint(
            "channel IN ('in_app', 'email')",
            name="chk_notification_channel_frequency_channel",
        ),
        sa.CheckConstraint(
            "frequency IN ('immediate', 'daily_digest', 'weekly')",
            name="chk_notification_channel_frequency_value",
        ),
        sa.Index("ix_notification_channel_frequency_user", "user_id"),
    )
