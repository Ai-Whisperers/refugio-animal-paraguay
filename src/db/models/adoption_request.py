"""SQLAlchemy ORM model for adoption requests."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class AdoptionRequestStatus(StrEnum):
    """Status values — must match chk_adoption_requests_status CHECK constraint exactly."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AdoptionRequest(Base):
    """Adoption application workflow — links adopters to animals with status tracking."""

    __tablename__ = "adoption_requests"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    animal_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", name="fk_adoption_requests_animal_id"),
        nullable=False,
    )
    adopter_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("adopters.id", name="fk_adoption_requests_adopter_id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="pending",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    contract_pdf_path: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    contract_generated_at: Mapped[datetime | None] = mapped_column(
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
    # Pipeline tracking — populated after migration 054
    current_stage_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey(
            "adoption_pipeline_stages.id",
            name="fk_adoption_requests_current_stage_id",
        ),
        nullable=True,
    )
    current_stage_started_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Relationships for ORM navigation
    animal: Mapped["Animal"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Animal",
        foreign_keys=[animal_id],
        back_populates="adoption_requests",
        lazy="select",
    )
    adopter: Mapped["Adopter"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Adopter",
        foreign_keys=[adopter_id],
        back_populates="adoption_requests",
        lazy="select",
    )
