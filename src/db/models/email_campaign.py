"""SQLAlchemy ORM model for email campaigns (scheduled sending).

An email campaign represents a scheduled or immediate send of an email
template to an email list. Tracks the lifecycle from draft through
scheduled → sending → sent (or failed/cancelled).
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class EmailCampaignStatus(enum.StrEnum):
    """Lifecycle status of an email campaign send."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EmailCampaign(Base):
    """An email campaign that sends a template to an email list.

    Campaigns reference an EmailList (RAP-215) and an EmailTemplate (RAP-216).
    They can be scheduled for a future time or triggered immediately.
    The sent_count and failed_count are updated as sending progresses.
    """

    __tablename__ = "email_campaigns"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # References to EmailList and EmailTemplate (stored as UUIDs, FK resolved at runtime)
    email_list_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("email_lists.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email_template_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="References email_templates.id — FK added after migrations merge",
    )

    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        default=EmailCampaignStatus.DRAFT,
        index=True,
    )

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
        comment="When to send. NULL means send immediately when triggered.",
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Metrics
    sent_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    failed_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_recipients: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Snapshot of list subscriber count at time of sending",
    )

    # Audit
    created_by_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    error_message: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
        comment="Last error message if campaign sending failed",
    )

    # Events (opens/clicks) recorded via tracking endpoints
    events: Mapped[list["EmailCampaignEvent"]] = relationship(  # noqa: F821
        "EmailCampaignEvent",
        back_populates="campaign",
        lazy="select",
        cascade="all, delete-orphan",
    )
