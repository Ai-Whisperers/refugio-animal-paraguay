"""Email verification service.

Handles creation and validation of email verification tokens.
Reuses the verification_tokens table with token_type = 'email_verification'.
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User
from src.db.models.verification_token import TokenType, VerificationToken

logger = logging.getLogger(__name__)

EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS = 24
TOKEN_BYTE_LENGTH = 32


class VerificationResult(StrEnum):
    """Possible outcomes of email verification."""

    SUCCESS = "success"
    TOKEN_NOT_FOUND = "invalid_token"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_ALREADY_USED = "token_already_used"
    USER_NOT_FOUND = "user_not_found"



async def create_email_verification_token(db: AsyncSession, user_id: str) -> str | None:
    """Create an email verification token for a user.

    Invalidates any existing unused verification tokens for this user.
    Returns the plain-text token string, or None if user not found.
    """
    user = await db.get(User, user_id)
    if user is None:
        return None

    # Invalidate existing unused email verification tokens
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user_id,
            VerificationToken.token_type == TokenType.EMAIL_VERIFICATION.value,
            VerificationToken.used_at.is_(None),
        )
    )
    for old_token in result.scalars().all():
        old_token.used_at = datetime.now(UTC)

    # Create new token
    token_value = secrets.token_urlsafe(TOKEN_BYTE_LENGTH)
    verification_token = VerificationToken(
        user_id=user_id,
        token=token_value,
        token_type=TokenType.EMAIL_VERIFICATION.value,
        expires_at=datetime.now(UTC) + timedelta(hours=EMAIL_VERIFICATION_TOKEN_EXPIRY_HOURS),
    )
    db.add(verification_token)
    await db.flush()

    logger.info("Email verification token created for user_id=%s", user_id)
    return token_value


async def verify_email(db: AsyncSession, token: str) -> VerificationResult:
    """Verify an email using a token.

    Validates the token, marks it as used, and sets user.email_verified = True.
    Returns a VerificationResult indicating the outcome.
    """
    # First check if the token exists at all (including used tokens)
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.token == token,
            VerificationToken.token_type == TokenType.EMAIL_VERIFICATION.value,
        )
    )
    token_record = result.scalar_one_or_none()

    if token_record is None:
        logger.warning("Email verification failed: token not found")
        return VerificationResult.TOKEN_NOT_FOUND

    # Check if token was already used
    if token_record.used_at is not None:
        logger.warning("Email verification failed: token already used")
        return VerificationResult.TOKEN_ALREADY_USED

    # Check if token is expired
    if token_record.expires_at < datetime.now(UTC):
        logger.warning("Email verification failed: token expired")
        return VerificationResult.TOKEN_EXPIRED

    user = await db.get(User, token_record.user_id)
    if user is None or not user.is_active:
        logger.warning(
            "Email verification failed: user not found or inactive, user_id=%s",
            token_record.user_id,
        )
        return VerificationResult.USER_NOT_FOUND

    # Already verified — idempotent success
    if user.email_verified:
        token_record.used_at = datetime.now(UTC)
        return VerificationResult.SUCCESS

    # Mark token as used and verify email
    token_record.used_at = datetime.now(UTC)
    user.email_verified = True

    logger.info("Email verified for user_id=%s", user.id)
    return VerificationResult.SUCCESS
