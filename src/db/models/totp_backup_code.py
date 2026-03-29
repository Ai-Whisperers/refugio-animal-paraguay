"""SQLAlchemy ORM model for TOTP 2FA backup/recovery codes."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base

BACKUP_CODE_COUNT = 10  # generated per batch


class TotpBackupCode(Base):
    """Single-use backup code for 2FA recovery.

    Codes are stored as bcrypt hashes. Once a code is consumed, ``used_at``
    is set and the code cannot be reused. Generating a new batch replaces
    all existing (unused or used) codes for that user.
    """

    __tablename__ = "totp_backup_codes"

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
    code_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    used_at: Mapped[datetime | None] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=True)
