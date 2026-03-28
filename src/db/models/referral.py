"""SQLAlchemy ORM model for referral tracking."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ReferralConversionType(StrEnum):
    """Type of conversion from a referral."""

    DONATION = "donation"
    ADOPTION_APPLICATION = "adoption_application"
    REGISTRATION = "registration"


class Referral(Base):
    """Tracks referral attributions — which shares led to conversions."""

    __tablename__ = "referrals"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    referrer_user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    referred_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    conversion_type: Mapped[str | None] = mapped_column(
        sa.String(30),
        nullable=True,
        index=True,
    )
    conversion_entity_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=True,
    )
    landing_path: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        sa.String(45),
        nullable=True,
    )
    converted_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        index=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "conversion_type IN ('donation', 'adoption_application', 'registration') "
            "OR conversion_type IS NULL",
            name="chk_referral_conversion_type_valid",
        ),
        sa.Index("ix_referrals_referrer_created", "referrer_user_id", "created_at"),
    )
