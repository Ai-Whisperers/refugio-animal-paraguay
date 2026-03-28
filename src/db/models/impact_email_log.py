"""SQLAlchemy ORM model for impact email logs."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class EmailStatus(StrEnum):
    """Delivery status of an impact email."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    BOUNCED = "bounced"
    FAILED = "failed"


VALID_EMAIL_STATUSES = {s.value for s in EmailStatus}


class ImpactEmailLog(Base):
    """Log of monthly impact emails sent to donors."""

    __tablename__ = "impact_email_logs"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    donor_id: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("donors.id"), nullable=False)
    email_address: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    subject: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    report_month: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    report_year: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    donation_total: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(3), nullable=False, default="PYG")
    animals_rescued: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    animals_adopted: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    castrations_funded: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    medical_treatments: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default=EmailStatus.PENDING.value
    )
    sent_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )

    __table_args__ = (
        sa.Index("ix_impact_email_logs_donor_id", "donor_id"),
        sa.Index("ix_impact_email_logs_status", "status"),
        sa.Index("ix_impact_email_logs_report_period", "report_year", "report_month"),
        sa.UniqueConstraint(
            "donor_id", "report_year", "report_month", name="uq_donor_report_period"
        ),
    )
