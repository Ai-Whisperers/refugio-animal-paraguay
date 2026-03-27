"""SQLAlchemy ORM model for phone verification OTPs."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class PhoneVerificationOTP(Base):
    """One-time password record for phone number verification via WhatsApp."""

    __tablename__ = "phone_verification_otps"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    phone: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, index=True
    )
    otp_hash: Mapped[str] = mapped_column(
        sa.String(255), nullable=False, comment="bcrypt hash of the 6-digit OTP"
    )
    attempted_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
