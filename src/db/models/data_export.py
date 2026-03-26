"""SQLAlchemy ORM model for GDPR data export requests."""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DataExportStatus(enum.StrEnum):
    """Status lifecycle for data export requests."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class DataSubjectType(enum.StrEnum):
    """Type of data subject requesting the export."""

    DONOR = "donor"
    ADOPTER = "adopter"
    STAFF = "staff"


class DataExportRequest(Base):
    """Tracks GDPR Article 15/20 data export requests.

    Each request records who asked, what type of subject they are,
    the status of the export, and the exported data (JSONB) once ready.
    """

    __tablename__ = "data_export_requests"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    # The staff user who initiated the request (or on behalf of the subject)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # The data subject whose data is being exported
    subject_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
    )
    # ID of the subject (donor_id, adopter_id, or user_id depending on subject_type)
    subject_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
    )
    # Email of the subject (denormalized for audit trail)
    subject_email: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=DataExportStatus.PENDING.value,
    )
    # Exported data stored as JSONB (no filesystem dependency)
    export_data: Mapped[dict | None] = mapped_column(
        sa.JSON,
        nullable=True,
    )
    # Error message if export failed
    error_message: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    # Tracking timestamps
    requested_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    downloaded_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "subject_type IN ('donor', 'adopter', 'staff')",
            name="chk_data_export_subject_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'expired')",
            name="chk_data_export_status",
        ),
        sa.Index("ix_data_export_subject", "subject_type", "subject_id"),
        sa.Index("ix_data_export_requested_by", "requested_by_user_id"),
    )
