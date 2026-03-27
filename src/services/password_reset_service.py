"""Password reset service: token generation, validation, and password update."""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import hash_password
from src.db.models.user import User
from src.db.models.verification_token import TokenType, VerificationToken

logger = logging.getLogger(__name__)

PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1
TOKEN_BYTE_LENGTH = 32


async def create_password_reset_token(
    db: AsyncSession,
    email: str,
) -> str | None:
    """Create a password reset token for the user with the given email.

    Returns the token string if user exists, None otherwise.
    Does NOT reveal whether the email exists (timing-safe).
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        return None

    # Invalidate any existing unused reset tokens for this user
    existing_tokens = await db.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user.id,
            VerificationToken.token_type == TokenType.PASSWORD_RESET.value,
            VerificationToken.used_at.is_(None),
        )
    )
    for existing_token in existing_tokens.scalars().all():
        existing_token.used_at = datetime.now(UTC)

    token_value = secrets.token_urlsafe(TOKEN_BYTE_LENGTH)
    verification_token = VerificationToken(
        user_id=user.id,
        token=token_value,
        token_type=TokenType.PASSWORD_RESET.value,
        expires_at=datetime.now(UTC) + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS),
    )
    db.add(verification_token)
    await db.flush()

    logger.info(
        "Password reset token created for user %s",
        str(user.id)[:8] + "...",
    )
    return token_value


async def validate_reset_token(
    db: AsyncSession,
    token: str,
) -> VerificationToken | None:
    """Validate a password reset token. Returns the token record if valid, None otherwise."""
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token == token,
            VerificationToken.token_type == TokenType.PASSWORD_RESET.value,
            VerificationToken.used_at.is_(None),
        )
    )
    verification_token = result.scalar_one_or_none()

    if verification_token is None:
        return None

    if verification_token.expires_at < datetime.now(UTC):
        return None

    return verification_token


async def reset_password(
    db: AsyncSession,
    token: str,
    new_password: str,
) -> bool:
    """Reset the user's password using a valid reset token.

    Returns True if successful, False if token is invalid/expired.
    """
    verification_token = await validate_reset_token(db, token)
    if verification_token is None:
        return False

    user = await db.get(User, verification_token.user_id)
    if user is None or not user.is_active:
        return False

    user.hashed_password = hash_password(new_password)
    verification_token.used_at = datetime.now(UTC)
    await db.flush()

    logger.info(
        "Password reset completed for user %s",
        str(user.id)[:8] + "...",
    )
    return True
