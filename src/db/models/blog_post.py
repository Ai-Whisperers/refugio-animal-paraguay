"""SQLAlchemy ORM model for blog/news posts."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class BlogPost(Base):
    """Blog/news post for community engagement."""

    __tablename__ = "blog_posts"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(sa.String(300), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(350), nullable=False, unique=True, index=True)
    body_html: Mapped[str] = mapped_column(sa.Text, nullable=False)
    author_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    featured_image_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    tags: Mapped[list] = mapped_column(
        sa.JSON,
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True, index=True
    )
    is_published: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false"), index=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, server_default=sa.text("false")
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

    __table_args__ = (sa.Index("ix_blog_posts_created_at", "created_at"),)
