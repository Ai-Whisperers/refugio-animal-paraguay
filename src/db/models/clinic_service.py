"""SQLAlchemy ORM model for veterinary clinic service catalog."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ServiceCategory(StrEnum):
    """Categories for clinic services."""

    CONSULTATION = "consultation"
    VACCINATION = "vaccination"
    SURGERY = "surgery"
    DENTAL = "dental"
    DIAGNOSTIC = "diagnostic"
    GROOMING = "grooming"
    EMERGENCY = "emergency"
    PREVENTIVE = "preventive"
    OTHER = "other"


class ClinicService(Base):
    """A service offered by a partner veterinary clinic with pricing.

    Each clinic maintains its own catalog of services. Services can be
    priced in PYG (Paraguayan Guarani) and optionally in EUR for
    international donors. Inactive services are hidden from public views
    but preserved for historical records.
    """

    __tablename__ = "clinic_services"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )

    # -- Relationship --
    clinic_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_clinics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -- Service details --
    name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    category: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
        server_default=sa.text("'other'"),
    )

    # -- Pricing --
    price_pyg: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        comment="Price in Paraguayan Guarani",
    )
    price_eur: Mapped[float | None] = mapped_column(
        sa.Numeric(10, 2),
        nullable=True,
        comment="Optional price in EUR for international donors",
    )

    # -- Duration --
    duration_minutes: Mapped[int | None] = mapped_column(
        sa.Integer,
        nullable=True,
        comment="Estimated duration in minutes",
    )

    # -- Status --
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.true(),
    )

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
            "category IN ('consultation', 'vaccination', 'surgery', 'dental', "
            "'diagnostic', 'grooming', 'emergency', 'preventive', 'other')",
            name="chk_clinic_services_category",
        ),
        sa.CheckConstraint("price_pyg >= 0", name="chk_clinic_services_price_pyg"),
        sa.CheckConstraint(
            "price_eur IS NULL OR price_eur >= 0",
            name="chk_clinic_services_price_eur",
        ),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="chk_clinic_services_duration",
        ),
        sa.Index("ix_clinic_services_clinic_id_category", "clinic_id", "category"),
        sa.Index("ix_clinic_services_active", "is_active"),
    )
