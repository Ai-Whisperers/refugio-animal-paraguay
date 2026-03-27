"""SQLAlchemy ORM model for active sessions (JWT session tracking)."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class ActiveSession(Base):
    """Tracks active JWT sessions for timeout enforcement and forced logout."""

    __tablename__ = "active_sessions"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    jti: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    last_activity: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(sa.String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(sa.String(512), nullable=True)
