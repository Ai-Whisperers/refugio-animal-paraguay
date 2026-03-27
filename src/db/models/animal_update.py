"""SQLAlchemy ORM models for animal update notifications sent to sponsors.

Animal updates are published by shelter staff and automatically trigger
email notifications to all active sponsors of the relevant animal.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AnimalUpdateType(enum.StrEnum):
    """Category of the update — used for filtering and display."""

    HEALTH = "health"
    BEHAVIOR = "behavior"
    MILESTONE = "milestone"
    GENERAL = "general"


class MilestoneType(enum.StrEnum):
    """Significant milestones tracked in milestone-type updates."""

    VACCINATION = "vaccination"
    MEDICAL_TREATMENT = "medical_treatment"
    BEHAVIORAL_PROGRESS = "behavioral_progress"
    ADOPTION_READY = "adoption_ready"
    BIRTHDAY = "birthday"
    RECOVERED = "recovered"
    DECEASED = "deceased"
    RETURNED_FROM_ADOPTION = "returned_from_adoption"


class SponsorNotificationFrequency(enum.StrEnum):
    """How often a sponsor wants to receive update emails."""

    IMMEDIATE = "immediate"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"
    MONTHLY_DIGEST = "monthly_digest"


class AnimalUpdate(Base):
    """A single update published by shelter staff about an animal.

    When published, all active sponsors of the animal receive an email
    (subject to their notification preferences).
    """

    __tablename__ = "animal_updates"

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
    # Staff user who published the update
    published_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    update_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="general",
    )
    # Populated when update_type == 'milestone'
    milestone_type: Mapped[str | None] = mapped_column(
        sa.String(50),
        nullable=True,
    )
    # Ordered list of photo URLs for this update
    photo_urls: Mapped[list | None] = mapped_column(
        sa.JSON,
        nullable=True,
        server_default="[]",
    )
    published_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )


class SponsorUpdatePreference(Base):
    """Per-sponsorship notification frequency preference.

    One row per sponsorship. Created with defaults on first save
    or upserted when sponsor updates preferences.
    """

    __tablename__ = "sponsor_update_preferences"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    sponsorship_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("sponsorships.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    notification_enabled: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    notification_frequency: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="immediate",
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
