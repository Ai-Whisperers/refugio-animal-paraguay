"""Service for generating, hashing, and validating verification tokens.

Tokens are generated as URL-safe random strings, but only their SHA-256
hashes are persisted to the database. This ensures that a database
compromise does not expose usable tokens.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.verification_token import TokenType, VerificationToken

TOKEN_BYTES = 32  # 256 bits of entropy
EMAIL_VERIFY_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_HOURS = 1


def generate_token() -> str:
    """Return a cryptographically secure URL-safe token string."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of *token*."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _expiry_for(token_type: TokenType) -> datetime:
    """Return the expiration datetime for the given token type."""
    hours = (
        EMAIL_VERIFY_EXPIRY_HOURS
        if token_type == TokenType.EMAIL_VERIFY
        else PASSWORD_RESET_EXPIRY_HOURS
    )
    return datetime.now(UTC) + timedelta(hours=hours)


async def create_verification_token(
    db: AsyncSession,
    user_id: UUID,
    token_type: TokenType,
) -> str:
    """Create a new verification token, invalidating any existing tokens of the same type.

    Returns the plaintext token (to be sent via email). Only the hash is stored.
    """
    # Delete any existing tokens of this type for the user
    await db.execute(
        delete(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.token_type == token_type.value,
        )
    )

    plaintext = generate_token()
    token_record = VerificationToken(
        user_id=user_id,
        token_hash=hash_token(plaintext),
        token_type=token_type.value,
        expires_at=_expiry_for(token_type),
    )
    db.add(token_record)
    await db.flush()
    return plaintext


async def validate_and_consume_token(
    db: AsyncSession,
    plaintext_token: str,
    expected_type: TokenType,
) -> UUID | None:
    """Validate a token and return the associated user_id, or None if invalid.

    A valid token is one that:
    - Exists in the database (hash matches)
    - Has the expected type
    - Has not expired

    On success the token is deleted (single-use).
    """
    token_hash = hash_token(plaintext_token)
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token_hash == token_hash,
            VerificationToken.token_type == expected_type.value,
        )
    )
    record = result.scalar_one_or_none()

    if record is None:
        return None

    if record.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        # Expired — clean up and reject
        await db.delete(record)
        await db.flush()
        return None

    user_id = record.user_id
    await db.delete(record)
    await db.flush()
    return user_id


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """Delete all expired tokens. Returns the number of tokens removed."""
    result = await db.execute(
        delete(VerificationToken).where(VerificationToken.expires_at < datetime.now(UTC))
    )
    await db.flush()
    return result.rowcount  # type: ignore[return-value]
