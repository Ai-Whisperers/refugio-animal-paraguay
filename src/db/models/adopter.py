"""SQLAlchemy ORM model for adopters."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Adopter(Base):
    """Adopter profile with GDPR consent tracking and soft-delete support."""

    __tablename__ = "adopters"

    id: Mapped[UUID] = mapped_column(
        sa.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )
    full_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
        unique=True,
    )
    phone: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Nullable: consent recorded when given, None means not yet obtained
    gdpr_consent_at: Mapped[datetime | None] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=True,
    )
    # Soft delete: set to timestamp when adopter requests data removal
    deleted_at: Mapped[datetime | None] = mapped_column(
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
