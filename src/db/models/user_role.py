"""SQLAlchemy ORM model for additional user roles (multi-role support)."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class UserRoleAssignment(Base):
    """Junction table linking users to additional roles.

    A user's primary role lives on the users.role column; this table tracks
    supplementary roles (e.g., an adopter who also volunteers and donates).
    """

    __tablename__ = "user_roles"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),
    )

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    user_id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        sa.String(50), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
