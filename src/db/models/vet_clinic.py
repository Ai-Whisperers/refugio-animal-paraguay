"""SQLAlchemy ORM model for partner veterinary clinics."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ClinicStatus(StrEnum):
    """Partner clinic registration status."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class VetClinic(Base):
    """A partner veterinary clinic that can redeem vouchers and provide services.

    Clinics go through a registration workflow: pending -> active.
    Staff/admin approve pending registrations. Suspended clinics cannot
    redeem vouchers until reactivated.
    """

    __tablename__ = "vet_clinics"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # -- Identity --
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    license_number: Mapped[str | None] = mapped_column(
        sa.String(100), nullable=True, unique=True
    )

    # -- Contact --
    email: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    contact_person: Mapped[str] = mapped_column(sa.String(200), nullable=False)

    # -- Address --
    address: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    city: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(
        sa.String(100), nullable=True, comment="Paraguayan department (state)"
    )
    latitude: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(sa.Float, nullable=True)

    # -- Capabilities --
    specialties: Mapped[str | None] = mapped_column(
        sa.Text, nullable=True, comment="Comma-separated list of specialties"
    )
    accepts_emergencies: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.false()
    )

    # -- Partnership --
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default=sa.text("'pending'")
    )
    partnership_start: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    partnership_end: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    # -- Timestamps --
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
            "status IN ('pending', 'active', 'suspended', 'inactive')",
            name="chk_vet_clinics_status",
        ),
        sa.Index("ix_vet_clinics_status", "status"),
        sa.Index("ix_vet_clinics_city", "city"),
    )
