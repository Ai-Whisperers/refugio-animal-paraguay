"""Email campaign event model — open and click tracking."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class EventType(enum.StrEnum):
    """Type of campaign engagement event."""

    OPEN = "open"
    CLICK = "click"


class CampaignVariant(enum.StrEnum):
    """A/B test variant label."""

    A = "a"
    B = "b"


class EmailCampaignEvent(Base):
    """Records an open or click event for an email campaign.

    Events are recorded via public tracking endpoints embedded in outbound
    emails (1x1 pixel for opens, redirect URL for clicks).
    """

    __tablename__ = "email_campaign_events"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    campaign_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("email_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        sa.String(10),
        nullable=False,
        comment="open or click",
    )
    recipient_email: Mapped[str | None] = mapped_column(
        sa.String(320),
        nullable=True,
        index=True,
    )
    clicked_url: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # A/B variant this event belongs to (null when A/B testing not active)
    variant: Mapped[str | None] = mapped_column(
        sa.String(1),
        nullable=True,
        comment="a or b for A/B test tracking",
    )
    ip_address: Mapped[str | None] = mapped_column(sa.String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    # Relationship back to the campaign
    campaign: Mapped["EmailCampaign"] = relationship(  # noqa: F821
        "EmailCampaign",
        back_populates="events",
        lazy="select",
    )

    __table_args__ = (
        sa.Index("ix_email_campaign_events_campaign_type", "campaign_id", "event_type"),
    )
