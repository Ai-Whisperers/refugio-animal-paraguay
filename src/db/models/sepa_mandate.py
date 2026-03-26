"""SQLAlchemy ORM model for SEPA Direct Debit mandates.

Tracks SEPA mandate lifecycle for recurring EU donations.
Mandates authorize the shelter to debit a donor's bank account.
"""

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class MandateStatus(enum.StrEnum):
    """SEPA mandate lifecycle status."""

    PENDING = "pending"  # SetupIntent created, awaiting confirmation
    ACTIVE = "active"  # Mandate confirmed, can process debits
    REVOKED = "revoked"  # Donor or staff revoked the mandate
    FAILED = "failed"  # SetupIntent or mandate setup failed


class SepaMandate(Base):
    """SEPA Direct Debit mandate — authorizes recurring debits from a donor's bank account.

    One mandate per donor (unique constraint). Mandate is created via Stripe
    SetupIntent flow and confirmed asynchronously via webhook.
    """

    __tablename__ = "sepa_mandates"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    donor_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("donors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Stripe identifiers for the mandate lifecycle
    stripe_customer_id: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    stripe_setup_intent_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
    )
    stripe_payment_method_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    stripe_mandate_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    # Masked IBAN for display — never store full IBAN
    iban_last4: Mapped[str | None] = mapped_column(
        sa.String(4),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="pending",
    )
    # Donation amount and interval for recurring debits
    amount_cents: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    interval: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="month",
    )
    # Stripe subscription ID (created after mandate is confirmed)
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        sa.String(500),
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

    donor: Mapped["Donor"] = relationship("Donor", lazy="select")  # noqa: F821

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'revoked', 'failed')",
            name="chk_sepa_mandates_status",
        ),
        sa.CheckConstraint(
            "interval IN ('month', 'year')",
            name="chk_sepa_mandates_interval",
        ),
        sa.CheckConstraint(
            "amount_cents > 0",
            name="chk_sepa_mandates_amount_positive",
        ),
    )
