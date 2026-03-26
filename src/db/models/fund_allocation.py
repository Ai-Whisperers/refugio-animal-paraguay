"""SQLAlchemy ORM model for fund allocation tracking.

Tracks shelter expenses by category (medical, food, operations, admin,
fundraising, other) for transparency reporting and EU compliance.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class FundCategory(enum.StrEnum):
    """Expense category for fund allocation transparency."""

    MEDICAL = "medical"
    FOOD = "food"
    OPERATIONS = "operations"
    ADMIN = "admin"
    FUNDRAISING = "fundraising"
    OTHER = "other"


class FundAllocation(Base):
    """Individual expense record categorized by fund type.

    Each allocation represents a shelter expense tagged with a category
    for transparency reporting, donor communications, and EU compliance.
    Amount stored as integer cents to avoid float precision loss.
    """

    __tablename__ = "fund_allocations"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    # Fund category for transparency breakdown
    category: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        index=True,
    )
    # Amount in smallest currency unit (cents for EUR/USD, guaranies for PYG)
    amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="PYG",
    )
    # Description of the expense
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    # Date the transaction occurred (may differ from created_at)
    transaction_date: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
    )
    # Staff member who recorded the allocation
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id"),
        nullable=True,
    )
    # Receipt or invoice reference number
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
