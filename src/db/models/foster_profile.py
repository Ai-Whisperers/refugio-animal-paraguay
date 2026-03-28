"""SQLAlchemy ORM model for foster family profiles (RAP-190).

Foster families temporarily care for animals at home while a permanent
adoption is arranged. This model tracks their application, home environment,
capacity, and approval status.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class FosterStatus(StrEnum):
    """Lifecycle status of a foster application."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    INACTIVE = "inactive"


class HomeType(StrEnum):
    """Type of housing the foster family has."""

    HOUSE_WITH_YARD = "house_with_yard"
    HOUSE_WITHOUT_YARD = "house_without_yard"
    APARTMENT = "apartment"
    FARM = "farm"
    OTHER = "other"


class AnimalTypePreference(StrEnum):
    """Animal types the foster family is willing to care for."""

    DOGS = "dogs"
    CATS = "cats"
    SMALL_ANIMALS = "small_animals"
    ANY = "any"


FOSTER_STATUS_VALUES = frozenset(s.value for s in FosterStatus)
HOME_TYPE_VALUES = frozenset(h.value for h in HomeType)
ANIMAL_TYPE_PREFERENCE_VALUES = frozenset(a.value for a in AnimalTypePreference)

FOSTER_MOTIVATION_MIN_LENGTH = 20
FOSTER_MOTIVATION_MAX_LENGTH = 2000
FOSTER_EXPERIENCE_MAX_LENGTH = 2000
FOSTER_REJECTION_REASON_MAX_LENGTH = 1000
FOSTER_MAX_ANIMALS_LIMIT = 20


class FosterProfile(Base):
    """Foster family profile — home environment, capacity, and approval status."""

    __tablename__ = "foster_profiles"

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
    # Motivation and experience
    motivation: Mapped[str] = mapped_column(sa.Text, nullable=False)
    experience_description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Home environment
    home_type: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=sa.text("'apartment'"),
    )
    has_outdoor_space: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
    )
    has_other_pets: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.false(),
    )
    other_pets_description: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    # Fostering capacity
    max_animals: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("1"),
    )
    preferred_animal_types: Mapped[list | None] = mapped_column(sa.JSON, nullable=True)
    # Status and review
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'pending'"),
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    reviewed_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
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
            "status IN ('pending', 'approved', 'rejected', 'inactive')",
            name="chk_foster_status_valid",
        ),
        sa.CheckConstraint(
            f"length(motivation) >= {FOSTER_MOTIVATION_MIN_LENGTH}",
            name="chk_foster_motivation_min_len",
        ),
        sa.CheckConstraint(
            f"max_animals >= 1 AND max_animals <= {FOSTER_MAX_ANIMALS_LIMIT}",
            name="chk_foster_max_animals_range",
        ),
        sa.CheckConstraint(
            "home_type IN ('house_with_yard', 'house_without_yard', 'apartment', 'farm', 'other')",
            name="chk_foster_home_type_valid",
        ),
    )
