"""SQLAlchemy ORM model for survey distribution tracking."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DistributionChannel(StrEnum):
    """Channels for survey distribution."""

    EMAIL = "email"
    WHATSAPP = "whatsapp"


class DeliveryStatus(StrEnum):
    """Delivery status of a survey distribution."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


VALID_CHANNELS = {c.value for c in DistributionChannel}
VALID_DELIVERY_STATUSES = {s.value for s in DeliveryStatus}


class SurveyDistribution(Base):
    """Tracks distribution of a survey to a recipient via email or WhatsApp."""

    __tablename__ = "survey_distributions"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    survey_id: Mapped[UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    recipient_email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    recipient_phone: Mapped[str | None] = mapped_column(sa.String(30), nullable=True)
    delivery_status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default=DeliveryStatus.PENDING.value
    )
    sent_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    failure_reason: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    sent_by: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )

    __table_args__ = (
        sa.Index("ix_survey_distributions_survey_id", "survey_id"),
        sa.Index("ix_survey_distributions_channel", "channel"),
        sa.Index("ix_survey_distributions_status", "delivery_status"),
    )
