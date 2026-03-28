"""SQLAlchemy ORM model for volunteer profiles."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class VolunteerStatus(StrEnum):
    """Volunteer application and activity status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    INACTIVE = "inactive"


class VolunteerAvailability(StrEnum):
    """When the volunteer is available."""

    WEEKDAY_MORNINGS = "weekday_mornings"
    WEEKDAY_AFTERNOONS = "weekday_afternoons"
    WEEKDAY_EVENINGS = "weekday_evenings"
    WEEKEND_MORNINGS = "weekend_mornings"
    WEEKEND_AFTERNOONS = "weekend_afternoons"
    FLEXIBLE = "flexible"


VOLUNTEER_SKILL_OPTIONS = frozenset(
    {
        "animal_care",
        "veterinary_assistance",
        "photography",
        "social_media",
        "transport_driving",
        "fundraising",
        "admin_office",
        "cleaning",
        "construction_maintenance",
        "education_outreach",
        "translation",
        "web_tech",
        "event_coordination",
    }
)


class VolunteerProfile(Base):
    """Volunteer profile — skills, availability, and application status."""

    __tablename__ = "volunteer_profiles"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # Application fields
    motivation: Mapped[str] = mapped_column(sa.Text, nullable=False)
    skills: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    availability: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    hours_per_week: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    # Emergency contact
    emergency_contact_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    # Status tracking
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
    )
    rejection_reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    # Activity stats
    total_hours_logged: Mapped[float] = mapped_column(
        sa.Numeric(8, 2), nullable=False, server_default=sa.text("0")
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
            "status IN ('pending', 'approved', 'rejected', 'inactive')",
            name="chk_volunteer_status_valid",
        ),
        sa.CheckConstraint(
            "length(motivation) >= 20",
            name="chk_volunteer_motivation_min_len",
        ),
        sa.CheckConstraint(
            "hours_per_week IS NULL OR (hours_per_week >= 1 AND hours_per_week <= 40)",
            name="chk_volunteer_hours_per_week_range",
        ),
    )
