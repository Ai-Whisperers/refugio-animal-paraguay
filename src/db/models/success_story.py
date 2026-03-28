"""SQLAlchemy ORM model for adoption success stories."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SuccessStory(Base):
    """Adoption success story for public inspiration."""

    __tablename__ = "success_stories"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    animal_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("animals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    adopter_name: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    story_text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    quote: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True, index=True
    )
    is_featured: Mapped[bool] = mapped_column(
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

    __table_args__ = (sa.Index("ix_success_stories_created_at", "created_at"),)
