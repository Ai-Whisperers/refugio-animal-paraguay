"""SQLAlchemy ORM model for external veterinary referrals."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class ReferralStatus(StrEnum):
    """Status of an external vet referral."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReferralUrgency(StrEnum):
    """Urgency level of the referral."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class VetReferral(Base):
    """Track referrals of shelter animals to external veterinary specialists."""

    __tablename__ = "vet_referrals"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    animal_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Referring user (shelter staff or vet who initiated the referral)
    referred_by_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # External vet details
    external_vet_name: Mapped[str] = mapped_column(
        sa.String(255), nullable=False
    )
    external_vet_clinic: Mapped[str | None] = mapped_column(
        sa.String(255), nullable=True
    )
    external_vet_phone: Mapped[str | None] = mapped_column(
        sa.String(50), nullable=True
    )
    external_vet_email: Mapped[str | None] = mapped_column(
        sa.String(255), nullable=True
    )

    # Referral details
    reason: Mapped[str] = mapped_column(sa.Text, nullable=False)
    specialty: Mapped[str | None] = mapped_column(
        sa.String(100), nullable=True
    )
    urgency: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="medium"
    )
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="pending"
    )

    # Scheduling
    appointment_date: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )

    # Outcome tracking
    diagnosis: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    treatment_notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )
    follow_up_date: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    estimated_cost: Mapped[float | None] = mapped_column(
        sa.Numeric(10, 2), nullable=True
    )
    actual_cost: Mapped[float | None] = mapped_column(
        sa.Numeric(10, 2), nullable=True
    )

    # Timestamps
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

    # Relationships
    animal = relationship("Animal", back_populates="vet_referrals")
    referred_by = relationship("User", lazy="selectin")
