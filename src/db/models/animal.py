"""SQLAlchemy ORM models for animals and animal photos."""

import enum
from datetime import date, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class AnimalSpecies(str, enum.Enum):
    """Species values — must match chk_animals_species CHECK constraint exactly."""

    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class AnimalStatus(str, enum.Enum):
    """Status values — must match chk_animals_status CHECK constraint exactly."""

    INTAKE = "intake"
    QUARANTINE = "quarantine"
    AVAILABLE = "available"
    FOSTER = "foster"
    UNDER_TREATMENT = "under_treatment"
    ADOPTED = "adopted"
    DECEASED = "deceased"


class AnimalPhoto(Base):
    """Gallery photo for an animal.

    URLs point to externally hosted images (Cloudinary). The API stores
    only the URL — upload is handled by the shelter client.
    """

    __tablename__ = "animal_photos"

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
    url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    caption: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    display_order: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    animal: Mapped["Animal"] = relationship("Animal", back_populates="photos")


class Animal(Base):
    """Animal record with species, status lifecycle, and optional medical info."""

    __tablename__ = "animals"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    species: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="dog",
    )
    status: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default="intake",
    )
    birth_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    primary_photo_url: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
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

    photos: Mapped[list[AnimalPhoto]] = relationship(
        AnimalPhoto,
        back_populates="animal",
        lazy="selectin",
        order_by=[AnimalPhoto.display_order.asc(), AnimalPhoto.created_at.asc()],
        cascade="all, delete-orphan",
    )

    # Back-reference from AdoptionRequest.animal
    adoption_requests: Mapped[list["AdoptionRequest"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AdoptionRequest",
        back_populates="animal",
        lazy="select",
    )
