"""SQLAlchemy ORM model for email verification and password reset tokens."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class TokenType(StrEnum):
    """Discriminator for token purpose."""

    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"


class VerificationToken(Base):
    """Time-limited token for email verification or password reset.

    The token_hash column stores a SHA-256 hash of the actual token.
    The plaintext token is never persisted — it is sent to the user via email
    and only the hash is stored for later comparison.
    """

    __tablename__ = "verification_tokens"

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
    token_hash: Mapped[str] = mapped_column(sa.String(64), nullable=False, unique=True)
    token_type: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(sa.TIMESTAMP(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
