"""SQLAlchemy ORM model for volunteer onboarding checklist items (RAP-642)."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

# ---------------------------------------------------------------------------
# Predefined onboarding item keys and their display titles
# ---------------------------------------------------------------------------

ONBOARDING_ITEMS: dict[str, str] = {
    "orientation": "Orientación general del refugio",
    "safety_training": "Capacitación en seguridad y primeros auxilios",
    "animal_handling": "Manejo seguro de animales",
    "shelter_rules": "Normas y código de conducta del refugio",
    "emergency_procedures": "Procedimientos de emergencia",
}

MANDATORY_ITEM_KEYS = frozenset(
    {
        "orientation",
        "safety_training",
        "animal_handling",
        "shelter_rules",
    }
)


class VolunteerOnboardingItem(Base):
    """Single checklist item in a volunteer's onboarding process."""

    __tablename__ = "volunteer_onboarding_items"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    volunteer_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("volunteer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_key: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        sa.String(200),
        nullable=False,
    )
    is_mandatory: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
    )
    completed: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    completed_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "volunteer_id",
            "item_key",
            name="uq_volunteer_onboarding_item",
        ),
    )
