"""SQLAlchemy ORM model for rescuer profiles."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class VerificationMethod(StrEnum):
    """How a rescuer was verified."""

    WHATSAPP = "whatsapp"
    SOCIAL = "social"
    MANUAL = "manual"


class RescuerProfile(Base):
    """Rescuer public profile with bio, location, social links, and counts."""

    __tablename__ = "rescuer_profiles"

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
    display_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(120), nullable=False, unique=True, index=True)
    bio: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    location_city: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    location_coords: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    social_links: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    phone_whatsapp: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    is_verified: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    verification_method: Mapped[str | None] = mapped_column(sa.String(20), nullable=True)
    animal_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    supporter_count: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default=sa.text("0")
    )
    joined_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
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
            "length(display_name) >= 2",
            name="chk_rescuer_display_name_min_len",
        ),
        sa.CheckConstraint(
            "length(display_name) <= 100",
            name="chk_rescuer_display_name_max_len",
        ),
        sa.CheckConstraint(
            "bio IS NULL OR length(bio) <= 1000",
            name="chk_rescuer_bio_max_len",
        ),
        sa.CheckConstraint(
            "animal_count >= 0",
            name="chk_rescuer_animal_count_positive",
        ),
        sa.CheckConstraint(
            "supporter_count >= 0",
            name="chk_rescuer_supporter_count_positive",
        ),
    )
