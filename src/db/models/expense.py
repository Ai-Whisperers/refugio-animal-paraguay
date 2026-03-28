"""SQLAlchemy ORM models for expenses and donation allocations."""

import enum
from datetime import date, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class ExpenseCategory(enum.StrEnum):
    """Expense categories for cost tracking."""

    FOOD = "food"
    MEDICAL = "medical"
    TRANSPORT = "transport"
    HOUSING = "housing"
    OTHER = "other"


class Expense(Base):
    """Expense record for tracking shelter costs.

    Links optional animal_id for animal-specific expenses (vet bills, etc.).
    """

    __tablename__ = "expenses"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    description: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    category: Mapped[str] = mapped_column(sa.String(20), nullable=False, index=True)
    # Amount in smallest currency unit (cents)
    amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    currency: Mapped[str] = mapped_column(
        sa.String(3),
        nullable=False,
        server_default="PYG",
    )
    expense_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    # Optional link to a specific animal
    related_animal_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Staff member who recorded the expense
    recorded_by_id: Mapped[UUID | None] = mapped_column(
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

    allocations: Mapped[list["DonationAllocation"]] = relationship(
        "DonationAllocation",
        back_populates="expense",
        lazy="select",
    )

    __table_args__ = (
        sa.CheckConstraint("amount_cents > 0", name="chk_expenses_amount_positive"),
        sa.CheckConstraint(
            "category IN ('food', 'medical', 'transport', 'housing', 'other')",
            name="chk_expenses_category",
        ),
    )


class DonationAllocation(Base):
    """Links a donation to an expense, tracking how donations are used.

    A single donation can be split across multiple expenses.
    """

    __tablename__ = "donation_allocations"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    donation_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expense_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Amount allocated from this donation to this expense (in cents)
    amount_cents: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    allocated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )

    donation: Mapped["Donation"] = relationship(  # noqa: F821
        "Donation",
        lazy="select",
    )
    expense: Mapped["Expense"] = relationship(
        "Expense",
        back_populates="allocations",
        lazy="select",
    )

    __table_args__ = (
        sa.CheckConstraint(
            "amount_cents > 0",
            name="chk_donation_allocations_amount_positive",
        ),
    )
