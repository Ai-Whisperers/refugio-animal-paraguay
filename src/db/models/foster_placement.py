"""SQLAlchemy ORM model for foster animal placements (RAP-191).

A foster placement records the assignment of an animal to an approved foster
family for a temporary care period.  When the animal is returned to the shelter
or adopted, the placement is closed by setting ended_at.
"""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class FosterPlacement(Base):
    """Active or historical assignment of an animal to a foster family."""

    __tablename__ = "foster_placements"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    foster_profile_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("foster_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    animal_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "animal_id",
            "ended_at",
            name="uq_foster_placement_active_animal",
            comment="Only one active (ended_at IS NULL) placement per animal",
        ),
    )
