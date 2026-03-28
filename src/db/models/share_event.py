"""SQLAlchemy ORM model for share event tracking."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ShareEntityType(StrEnum):
    """Type of entity being shared."""

    ANIMAL = "animal"
    CAMPAIGN = "campaign"
    STORY = "story"
    BLOG_POST = "blog_post"


class SharePlatform(StrEnum):
    """Platform used for sharing."""

    WHATSAPP = "whatsapp"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    COPY_LINK = "copy_link"
    NATIVE_SHARE = "native_share"


class ShareEvent(Base):
    """Immutable share event log — tracks content sharing across platforms."""

    __tablename__ = "share_events"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    entity_type: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        sa.String(20),
        nullable=False,
        index=True,
    )
    sharer_user_id: Mapped[UUID | None] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        sa.String(45),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        index=True,
    )

    __table_args__ = (
        sa.CheckConstraint(
            "entity_type IN ('animal', 'campaign', 'story', 'blog_post')",
            name="chk_share_entity_type_valid",
        ),
        sa.CheckConstraint(
            "platform IN ('whatsapp', 'facebook', 'twitter', 'copy_link', 'native_share')",
            name="chk_share_platform_valid",
        ),
        sa.Index("ix_share_events_entity", "entity_type", "entity_id"),
        sa.Index("ix_share_events_created_date", "created_at"),
    )
