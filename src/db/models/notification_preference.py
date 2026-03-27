"""SQLAlchemy ORM model for notification preferences.

Stores per-user, per-notification-type, per-channel opt-in/opt-out settings.
Users can control which notification categories they receive through
each delivery channel (in-app, email).
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class NotificationChannel(enum.StrEnum):
    """Delivery channels for notifications."""

    IN_APP = "in_app"
    EMAIL = "email"


class NotificationPreference(Base):
    """Per-user notification preference for a specific type and channel.

    Each row represents whether a user wants to receive a specific
    notification type through a specific channel. Missing rows are
    treated as enabled (opt-out model).
    """

    __tablename__ = "notification_preferences"

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
    notification_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.true(),
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
            "notification_type",
            "channel",
            name="uq_notification_pref_user_type_channel",
        ),
        sa.CheckConstraint(
            "channel IN ('in_app', 'email')",
            name="chk_notification_pref_channel",
        ),
        sa.CheckConstraint(
            "notification_type IN ("
            "'adoption_request_created', 'adoption_status_changed', "
            "'donation_received', 'donation_refunded', "
            "'animal_intake_completed', 'animal_status_changed', "
            "'system_alert', 'gdpr_request')",
            name="chk_notification_pref_type",
        ),
        sa.Index("ix_notification_pref_user", "user_id"),
    )
