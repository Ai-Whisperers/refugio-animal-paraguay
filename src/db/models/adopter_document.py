"""SQLAlchemy ORM model for documents uploaded by adopters."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class AdopterDocumentType(StrEnum):
    """Types of documents an adopter may submit."""

    IDENTITY = "identity"
    PROOF_OF_RESIDENCE = "proof_of_residence"
    INCOME_STATEMENT = "income_statement"
    VETERINARY_REFERENCE = "veterinary_reference"
    CHARACTER_REFERENCE = "character_reference"
    OTHER = "other"


class AdopterDocument(Base):
    """Document uploaded by an adopter to support their adoption application."""

    __tablename__ = "adopter_documents"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    adopter_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("adopters.id", ondelete="CASCADE"),
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
        server_default=AdopterDocumentType.OTHER.value,
    )
    description: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    uploaded_by_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
