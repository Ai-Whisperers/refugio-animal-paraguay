"""SQLAlchemy ORM models for CMS content management."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ContentType(StrEnum):
    """Type of CMS content."""

    PAGE = "page"
    BLOG_POST = "blog_post"
    SUCCESS_STORY = "success_story"
    ANNOUNCEMENT = "announcement"
    FAQ = "faq"


class ContentStatus(StrEnum):
    """Publication status of content."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentLanguage(StrEnum):
    """Supported content languages."""

    ES = "es"  # Spanish (default — Paraguay)
    EN = "en"  # English (EU donors)
    DE = "de"  # German (EU donors)
    NL = "nl"  # Dutch (founder's network)


class TranslationStatus(StrEnum):
    """Translation lifecycle status."""

    ORIGINAL = "original"  # Source language version
    TRANSLATED = "translated"  # Translation complete
    PENDING = "pending"  # Translation needed
    OUTDATED = "outdated"  # Original updated after translation


class CMSContent(Base):
    """CMS content item — pages, blog posts, success stories, announcements."""

    __tablename__ = "cms_contents"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    content_type: Mapped[str] = mapped_column(
        sa.String(30),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        sa.String(200),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        sa.String(300),
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'draft'"),
        index=True,
    )
    featured_image_url: Mapped[str | None] = mapped_column(
        sa.String(500),
        nullable=True,
    )
    meta_description: Mapped[str | None] = mapped_column(
        sa.String(300),
        nullable=True,
    )
    tags: Mapped[list | None] = mapped_column(
        sa.JSON,
        nullable=True,
    )
    language: Mapped[str] = mapped_column(
        sa.String(5),
        nullable=False,
        server_default=sa.text("'es'"),
        index=True,
    )
    translation_status: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        server_default=sa.text("'original'"),
    )
    source_content_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("cms_contents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    author_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        server_default=sa.text("0"),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
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

    __table_args__ = (
        sa.CheckConstraint(
            "content_type IN ('page', 'blog_post', 'success_story', 'announcement', 'faq')",
            name="chk_cms_content_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="chk_cms_status_valid",
        ),
        sa.CheckConstraint(
            "length(title) >= 1",
            name="chk_cms_title_not_empty",
        ),
        sa.CheckConstraint(
            "length(title) <= 300",
            name="chk_cms_title_max_len",
        ),
        sa.CheckConstraint(
            "language IN ('es', 'en', 'de', 'nl')",
            name="chk_cms_language_valid",
        ),
        sa.CheckConstraint(
            "translation_status IN ('original', 'translated', 'pending', 'outdated')",
            name="chk_cms_translation_status_valid",
        ),
        sa.UniqueConstraint("slug", "language", name="uq_cms_contents_slug_language"),
        sa.Index("ix_cms_contents_type_status", "content_type", "status"),
        sa.Index("ix_cms_contents_published_at", "published_at"),
    )
