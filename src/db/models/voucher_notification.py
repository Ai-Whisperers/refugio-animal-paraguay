"""SQLAlchemy ORM model for voucher notification events.

Tracks notification events for donor transparency: voucher claimed,
redeemed, and monthly summaries. Supports retry logic and rate limiting.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class VoucherNotificationType(StrEnum):
    """Types of voucher notification events."""

    VOUCHER_CLAIMED = "voucher_claimed"
    VOUCHER_REDEEMED = "voucher_redeemed"
    MONTHLY_SUMMARY = "monthly_summary"


class NotificationChannel(StrEnum):
    """Notification delivery channels."""

    EMAIL = "email"
    WHATSAPP = "whatsapp"


class NotificationStatus(StrEnum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


MAX_RETRY_COUNT = 3


class VoucherNotification(Base):
    """A notification event related to voucher lifecycle.

    Created when a voucher is claimed or redeemed, or for monthly
    donor summaries. Tracks delivery status and retry attempts.
    """

    __tablename__ = "voucher_notifications"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # -- Target user (donor) --
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Donor receiving the notification",
    )

    # -- Event type --
    event_type: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        comment="Type of notification event",
    )

    # -- Related voucher (nullable for monthly summaries) --
    voucher_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_vouchers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Related voucher (NULL for monthly summaries)",
    )

    # -- Delivery --
    channel: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'email'"),
        comment="Delivery channel: email or whatsapp",
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
        comment="Delivery status",
    )
    retry_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
        comment="Number of delivery attempts",
    )

    # -- Content snapshot --
    subject: Mapped[str | None] = mapped_column(
        sa.String(200),
        nullable=True,
        comment="Email subject line",
    )
    body_preview: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
        comment="Preview of notification content",
    )

    # -- Context data (JSON for template rendering) --
    context_data: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        comment="JSON context for template rendering",
    )

    # -- Timestamps --
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="When notification was successfully delivered",
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        comment="When the last delivery attempt was made",
    )

    __table_args__ = (
        sa.CheckConstraint(
            "event_type IN ('voucher_claimed', 'voucher_redeemed', 'monthly_summary')",
            name="chk_voucher_notifications_event_type",
        ),
        sa.CheckConstraint(
            "channel IN ('email', 'whatsapp')",
            name="chk_voucher_notifications_channel",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'skipped')",
            name="chk_voucher_notifications_status",
        ),
        sa.CheckConstraint(
            "retry_count >= 0",
            name="chk_voucher_notifications_retry_count",
        ),
        sa.Index("ix_voucher_notifications_user_status", "user_id", "status"),
        sa.Index("ix_voucher_notifications_created_at", "created_at"),
    )
