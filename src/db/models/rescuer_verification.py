"""SQLAlchemy ORM model for rescuer verification requests."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class VerificationStatus(StrEnum):
    """Status of a rescuer verification request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class VerificationMethod(StrEnum):
    """Method used for rescuer verification."""

    WHATSAPP = "whatsapp"
    SOCIAL = "social"
    MANUAL = "manual"


class RescuerVerificationRequest(Base):
    """Tracks rescuer verification submissions and admin decisions."""

    __tablename__ = "rescuer_verification_requests"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    rescuer_profile_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("rescuer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
    )
    evidence_url: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    evidence_notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    reviewer_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    __table_args__ = (
        sa.CheckConstraint(
            "method IN ('whatsapp', 'social', 'manual')",
            name="chk_verification_method_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="chk_verification_status_valid",
        ),
    )
