"""SQLAlchemy ORM model for in-app notifications.

Stores persistent notifications for staff and admin users. Notifications
are created by event bus handlers or direct service calls, and surfaced
via the notifications API.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class NotificationType(enum.StrEnum):
    """Categories of in-app notifications."""

    # Adoption events
    ADOPTION_REQUEST_CREATED = "adoption_request_created"
    ADOPTION_STATUS_CHANGED = "adoption_status_changed"

    # Donation events
    DONATION_RECEIVED = "donation_received"
    DONATION_REFUNDED = "donation_refunded"

    # Animal events
    ANIMAL_INTAKE_COMPLETED = "animal_intake_completed"
    ANIMAL_STATUS_CHANGED = "animal_status_changed"

    # Volunteer shift events
    VOLUNTEER_SHIFT_REMINDER = "volunteer_shift_reminder"

    # System / administrative
    SYSTEM_ALERT = "system_alert"
    GDPR_REQUEST = "gdpr_request"


class Notification(Base):
    """Persistent in-app notification for a user.

    Notifications are append-only from the perspective of creation. Users
    can mark them as read or delete them, but the original content is
    never modified.
    """

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
    )
    read_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "notification_type IN ("
            "'adoption_request_created', 'adoption_status_changed', "
            "'donation_received', 'donation_refunded', "
            "'animal_intake_completed', 'animal_status_changed', "
            "'system_alert', 'gdpr_request')",
            name="chk_notification_type",
        ),
        sa.Index("ix_notifications_user_read", "user_id", "is_read"),
        sa.Index("ix_notifications_user_created", "user_id", "created_at"),
    )
