"""SQLAlchemy ORM model for fund allocation (expense) tracking."""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class FundCategory(enum.StrEnum):
    """Fund allocation categories for transparency reporting."""

    MEDICAL = "medical"
    FOOD = "food"
    OPERATIONS = "operations"
    ADMIN = "admin"
    FUNDRAISING = "fundraising"
    OTHER = "other"


class FundAllocation(Base):
    """An expense or fund allocation record categorised for donor transparency.

    Tracks how donated funds are spent across shelter operations.
    Amount stored as integer cents to match Donation model precision.
    """

    __tablename__ = "fund_allocations"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    category: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        comment="Expense amount in cents (same precision as donations)",
    )
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="PYG",
    )
    description: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    transaction_date: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", name="fk_fund_allocations_recorded_by"),
        nullable=True,
    )
    receipt_reference: Mapped[str | None] = mapped_column(
        sa.String(100),
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
