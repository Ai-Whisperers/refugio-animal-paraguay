"""Password reset service: token generation, validation, and password update.

Security properties:
  - Tokens generated with secrets.token_urlsafe (>= 128 bits entropy)
  - Stored as SHA-256 hashes — plaintext never persisted
  - Expire after PASSWORD_RESET_TOKEN_EXPIRY_MINUTES (default 60)
  - All user tokens deleted on successful reset (single-use)
  - Generic responses prevent account enumeration
"""

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import hash_password, verify_password
from src.db.models.password_reset_token import PasswordResetToken
from src.db.models.user import User

logger = logging.getLogger(__name__)

# Token configuration
PASSWORD_RESET_TOKEN_BYTES = 32  # 256 bits of entropy via token_urlsafe
PASSWORD_RESET_TOKEN_EXPIRY_MINUTES = 60  # 1 hour


def generate_reset_token() -> str:
    """Generate a cryptographically secure URL-safe reset token."""
    return secrets.token_urlsafe(PASSWORD_RESET_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a plaintext token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_token_compare(token_hash_a: str, token_hash_b: str) -> bool:
    """Compare two token hashes in constant time to prevent timing attacks."""
    return hmac.compare_digest(token_hash_a, token_hash_b)


async def create_password_reset_token(
    db: AsyncSession,
    email: str,
) -> str | None:
    """Create a password reset token for the user with the given email.

    Returns the plaintext token if user exists and is active, None otherwise.
    The caller must not reveal whether a token was created (anti-enumeration).
    """
    normalized_email = email.strip().lower()

    result = await db.execute(
        select(User).where(User.email == normalized_email, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    # Generate token and store hash
    plaintext_token = generate_reset_token()
    token_hash = hash_token(plaintext_token)
    expires_at = datetime.now(UTC) + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRY_MINUTES)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(reset_token)
    await db.flush()

    logger.info(
        "Password reset token created for user_id=%s",
        user.id,
    )
    return plaintext_token


async def validate_and_reset_password(
    db: AsyncSession,
    plaintext_token: str,
    new_password: str,
) -> bool:
    """Validate a reset token and update the user's password.

    Returns True on success, False if token is invalid/expired.
    On success, all tokens for that user are deleted.
    """
    token_hash = hash_token(plaintext_token)

    # Look up the token — include expiry check in query
    now = datetime.now(UTC)
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.expires_at > now,
        )
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        logger.warning("Password reset attempted with invalid or expired token")
        return False

    # Constant-time verify the hash matches (defense in depth)
    if not constant_time_token_compare(reset_token.token_hash, token_hash):
        return False

    # Load the user
    user = await db.get(User, reset_token.user_id)
    if user is None or not user.is_active:
        logger.warning(
            "Password reset token valid but user inactive or missing, user_id=%s",
            reset_token.user_id,
        )
        return False

    # Check new password is different from current
    if verify_password(new_password, user.hashed_password):
        # Caller should handle this as a validation error, not a generic failure
        raise PasswordUnchangedError

    # Update password
    user.hashed_password = hash_password(new_password)

    # Delete ALL tokens for this user (single-use + invalidate siblings)
    await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id))

    await db.flush()

    logger.info(
        "Password reset completed for user_id=%s",
        user.id,
    )
    return True


class PasswordUnchangedError(Exception):
    """Raised when the new password matches the current password."""
