"""SQLAlchemy ORM model for medical documents attached to vet visits."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class DocumentType(StrEnum):
    """Types of medical documents."""

    VACCINATION = "vaccination"
    SURGERY_REPORT = "surgery_report"
    HEALTH_CERT = "health_cert"
    LAB_RESULT = "lab_result"
    XRAY = "xray"
    OTHER = "other"


class VetDocument(Base):
    """Medical document record linked to a vet visit."""

    __tablename__ = "vet_documents"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    vet_visit_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("vet_visits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        server_default=DocumentType.OTHER.value,
    )
    description: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    uploaded_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_virus_scanned: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
