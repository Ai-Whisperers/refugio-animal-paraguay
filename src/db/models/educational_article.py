"""SQLAlchemy ORM model for educational articles."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ArticleCategory(StrEnum):
    """Categories for educational articles."""

    PET_CARE = "pet_care"
    NUTRITION = "nutrition"
    HEALTH = "health"
    TRAINING = "training"
    ADOPTION = "adoption"
    LEGAL = "legal"
    GENERAL = "general"


class ArticleStatus(StrEnum):
    """Publication status for articles."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


VALID_CATEGORIES = {c.value for c in ArticleCategory}
VALID_STATUSES = {s.value for s in ArticleStatus}


class EducationalArticle(Base):
    """An educational article about pet care and animal welfare."""

    __tablename__ = "educational_articles"

    id: Mapped[UUID] = mapped_column(
        sa.Uuid, primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(255), nullable=False, unique=True)
    summary: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    category: Mapped[str] = mapped_column(
        sa.String(50), nullable=False, default=ArticleCategory.GENERAL.value
    )
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    cover_image_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, default=ArticleStatus.DRAFT.value
    )
    author_id: Mapped[UUID] = mapped_column(sa.Uuid, sa.ForeignKey("users.id"), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()
    )

    __table_args__ = (
        sa.Index("ix_educational_articles_category", "category"),
        sa.Index("ix_educational_articles_status", "status"),
        sa.Index("ix_educational_articles_slug", "slug"),
    )
