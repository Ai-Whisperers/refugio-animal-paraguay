"""SQLAlchemy ORM model for configurable adoption requirements.

Adoption requirements define conditions that adopters must meet,
either globally (animal_id=NULL) or per-animal. Requirements use
a type+JSON value pattern for flexible configuration.
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class RequirementType(StrEnum):
    """Types of adoption requirements."""

    YARD_REQUIRED = "yard_required"
    NO_CHILDREN_UNDER = "no_children_under"
    EXPERIENCE_REQUIRED = "experience_required"
    HOME_TYPE = "home_type"
    MAX_HOURS_ALONE = "max_hours_alone"
    OTHER_PETS_OK = "other_pets_ok"
    HOUSING_STATUS = "housing_status"
    INCOME_REQUIREMENT = "income_requirement"


# Human-readable descriptions for each requirement type
REQUIREMENT_DESCRIPTIONS: dict[str, str] = {
    RequirementType.YARD_REQUIRED: "Yard or outdoor space requirement",
    RequirementType.NO_CHILDREN_UNDER: "Minimum age of children in household",
    RequirementType.EXPERIENCE_REQUIRED: "Pet ownership experience level",
    RequirementType.HOME_TYPE: "Allowed home types",
    RequirementType.MAX_HOURS_ALONE: "Maximum hours the pet would be left alone daily",
    RequirementType.OTHER_PETS_OK: "Compatible pet types in household",
    RequirementType.HOUSING_STATUS: "Home ownership status",
    RequirementType.INCOME_REQUIREMENT: "Minimum monthly income requirement",
}


class AdoptionRequirement(Base):
    """A configurable adoption requirement.

    Requirements can be global (animal_id=NULL) or animal-specific.
    Animal-specific requirements override global requirements of the
    same type when merging.
    """

    __tablename__ = "adoption_requirements"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # NULL = global requirement, set = animal-specific
    animal_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL for global requirements, set for animal-specific",
    )

    requirement_type: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        comment="Type of requirement (e.g. yard_required, home_type)",
    )

    # JSONB value — schema depends on requirement_type
    value: Mapped[dict] = mapped_column(
        sa.JSON,
        nullable=False,
        comment="JSON value whose schema depends on requirement_type",
    )

    is_mandatory: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
        comment="If true, disqualifies adopter; if false, reduces match score",
    )

    active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("true"),
        comment="Soft-delete flag",
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
            "requirement_type IN ("
            "'yard_required', 'no_children_under', 'experience_required', "
            "'home_type', 'max_hours_alone', 'other_pets_ok', "
            "'housing_status', 'income_requirement')",
            name="chk_adoption_requirements_type",
        ),
        sa.Index("ix_adoption_requirements_animal_type", "animal_id", "requirement_type"),
    )
