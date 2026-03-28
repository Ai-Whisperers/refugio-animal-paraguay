"""SQLAlchemy ORM model for castration campaigns.

Extends Campaign concept with castration-specific fields: target/completed
counts, partner clinics (M2M), target area, and date range.
"""

from datetime import date, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base

# --- Campaign status labels (computed from dates, not stored) ---
CAMPAIGN_STATUS_PLANNED = "planned"
CAMPAIGN_STATUS_ACTIVE = "active"
CAMPAIGN_STATUS_COMPLETED = "completed"


class CastrationCampaignClinic(Base):
    """Junction table linking castration campaigns to partner vet clinics."""

    __tablename__ = "castration_campaign_clinics"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    campaign_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("castration_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinic_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.UniqueConstraint("campaign_id", "clinic_id", name="uq_castration_campaign_clinic"),
    )


class CastrationCampaign(Base):
    """Castration campaign — organized spay/neuter effort with target counts and partner clinics."""

    __tablename__ = "castration_campaigns"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    goal_message: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    target_count: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    completed_count: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    target_area: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    end_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
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

    # M2M relationship to VetClinic via junction table
    partner_clinics: Mapped[list["CastrationCampaignClinic"]] = relationship(
        "CastrationCampaignClinic",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        sa.CheckConstraint("target_count > 0", name="chk_castration_target_positive"),
        sa.CheckConstraint("completed_count >= 0", name="chk_castration_completed_non_negative"),
        sa.CheckConstraint("end_date > start_date", name="chk_castration_dates_valid"),
    )

    @property
    def status(self) -> str:
        """Compute campaign status from dates."""
        today = date.today()
        if today < self.start_date:
            return CAMPAIGN_STATUS_PLANNED
        if today > self.end_date:
            return CAMPAIGN_STATUS_COMPLETED
        return CAMPAIGN_STATUS_ACTIVE

    @property
    def progress_percent(self) -> int:
        """Compute progress as percentage of target."""
        if self.target_count <= 0:
            return 0
        raw = int((self.completed_count / self.target_count) * 100)
        return min(raw, 100)
