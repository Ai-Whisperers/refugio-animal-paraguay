"""SQLAlchemy ORM model for Web Push notification subscriptions.

Stores browser push subscription details (endpoint, keys) for donors
who opt in to receiving push notifications about emergencies, campaigns,
and donation-related updates.
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class PushSubscription(Base):
    """Web Push subscription for a donor.

    Each row stores the push subscription object from the browser's
    PushManager API. A single donor may have multiple active subscriptions
    (one per browser/device).
    """

    __tablename__ = "push_subscriptions"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    donor_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The push service endpoint URL from the browser
    endpoint: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    # ECDH public key for message encryption (base64url-encoded)
    p256dh_key: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    # Authentication secret (base64url-encoded)
    auth_key: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    # User agent string for identifying the browser/device
    user_agent: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    # Whether this subscription is still active
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    # Track push delivery failures
    failure_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "donor_id",
            "endpoint",
            name="uq_push_sub_donor_endpoint",
        ),
        sa.Index("ix_push_sub_active_donor", "donor_id", "is_active"),
    )
