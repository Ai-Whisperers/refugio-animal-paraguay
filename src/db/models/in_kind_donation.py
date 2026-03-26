"""SQLAlchemy ORM model for in-kind (non-cash) donations.

Tracks physical goods and services donated to the shelter with
estimated monetary values for impact reporting.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class ItemType(enum.StrEnum):
    """Categories for in-kind donation items."""

    FOOD = "food"
    MEDICATION = "medication"
    EQUIPMENT = "equipment"
    TOYS = "toys"
    BEDDING = "bedding"
    SUPPLIES = "supplies"
    VETERINARY_SERVICES = "veterinary_services"
    TRANSPORTATION = "transportation"
    OTHER = "other"


class InKindDonation(Base):
    """Non-cash donation record.

    Tracks physical goods and services received by the shelter.
    Estimated value stored as integer cents for consistency with
    the cash donation model.
    """

    __tablename__ = "in_kind_donations"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    # Optional link to existing donor; None = anonymous in-kind donation
    donor_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        sa.String(500),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default="1",
    )
    # Estimated monetary value in smallest currency unit (cents/guaranies)
    estimated_value_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="PYG",
    )
    date_received: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    # Staff member who received/recorded the donation
    received_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
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

    donor: Mapped["Donor | None"] = relationship(  # noqa: F821
        "Donor",
        lazy="select",
    )

    __table_args__ = (
        sa.Index("ix_in_kind_donations_donor_id_date", "donor_id", "date_received"),
        sa.Index("ix_in_kind_donations_item_type", "item_type"),
    )
