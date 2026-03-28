"""SQLAlchemy ORM model for uploaded media files."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class MediaContentType:
    """Allowed MIME types for media uploads."""

    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"

    ALL: frozenset[str] = frozenset({JPEG, PNG, WEBP})


class OptimizationStatus(StrEnum):
    """Optimization pipeline status for a media record."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class Media(Base):
    """Metadata record for an uploaded media file (image, document, etc.)."""

    __tablename__ = "media"

    __table_args__ = (
        sa.CheckConstraint(
            "size_bytes > 0",
            name="chk_media_size_positive",
        ),
        sa.CheckConstraint(
            "width > 0 AND height > 0",
            name="chk_media_dimensions_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    original_filename: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
        unique=True,
    )
    content_type: Mapped[str] = mapped_column(
        sa.String(50),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    width: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    height: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
    )
    uploaded_by: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    has_optimized: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    has_thumbnail: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        server_default=sa.text("false"),
    )
    optimization_status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default="pending",
    )
    optimized_path: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    thumbnail_path: Mapped[str | None] = mapped_column(
        sa.Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
