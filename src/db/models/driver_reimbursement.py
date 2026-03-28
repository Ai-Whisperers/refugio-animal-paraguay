"""SQLAlchemy ORM model for driver reimbursements."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ReimbursementStatus(StrEnum):
    """Status of a reimbursement request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ExpenseType(StrEnum):
    """Types of reimbursable transport expenses."""

    FUEL = "fuel"
    TOLLS = "tolls"
    PARKING = "parking"
    VEHICLE_RENTAL = "vehicle_rental"
    MAINTENANCE = "maintenance"
    OTHER = "other"


VALID_STATUSES = {s.value for s in ReimbursementStatus}
VALID_EXPENSE_TYPES = {e.value for e in ExpenseType}


class DriverReimbursement(Base):
    """A reimbursement request for transport-related expenses."""

    __tablename__ = "driver_reimbursements"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    transport_request_id: Mapped[UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("transport_requests.id"), nullable=False
    )
    driver_id: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("users.id"), nullable=False)
    expense_type: Mapped[str] = mapped_column(
        sa.String(30), nullable=False, default=ExpenseType.FUEL.value
    )
    amount: Mapped[float] = mapped_column(sa.Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False, default="PYG")
    description: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default=ReimbursementStatus.PENDING.value
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    __table_args__ = (
        sa.Index("ix_driver_reimbursements_status", "status"),
        sa.Index("ix_driver_reimbursements_driver_id", "driver_id"),
        sa.Index("ix_driver_reimbursements_transport_id", "transport_request_id"),
    )
