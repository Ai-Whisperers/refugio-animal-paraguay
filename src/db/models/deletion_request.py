"""SQLAlchemy ORM model for GDPR data deletion requests (Article 17)."""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DeletionRequestStatus(enum.StrEnum):
    """Status lifecycle for data deletion requests."""

    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    DENIED = "denied"


class DeletionRequest(Base):
    """Tracks GDPR Article 17 data deletion (right to erasure) requests.

    Deletion follows a two-step process: request (by subject or staff)
    then approval (by staff). Approved requests anonymize financial
    records and hard-delete personal data.
    """

    __tablename__ = "deletion_requests"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    # The data subject type and ID (same pattern as data_export_requests)
    subject_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
    )
    subject_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
    )
    # Email captured at request time for audit (since profile will be deleted)
    subject_email: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    # Optional reason from the data subject
    reason: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=DeletionRequestStatus.PENDING.value,
    )
    # Staff user who initiated or approved the request
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Denial reason (if denied)
    denial_reason: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "subject_type IN ('donor', 'adopter', 'staff')",
            name="chk_deletion_request_subject_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'executed', 'cancelled', 'denied')",
            name="chk_deletion_request_status",
        ),
        sa.Index("ix_deletion_request_subject", "subject_type", "subject_id"),
        sa.Index("ix_deletion_request_status", "status"),
    )
