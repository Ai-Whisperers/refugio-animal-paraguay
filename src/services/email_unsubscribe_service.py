"""Email unsubscribe service.

Provides one-click email unsubscribe via signed JWT tokens.
Users can request a signed unsubscribe URL (authenticated),
then click it to disable all email notifications without logging in.

Token format: JWT with sub=<user_id>, purpose="unsubscribe", 30-day expiry.

Functions:
    generate_unsubscribe_token  -- create a signed unsubscribe JWT
    validate_unsubscribe_token  -- decode and validate an unsubscribe JWT
    unsubscribe_all_email       -- disable all email notification preferences
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

import sqlalchemy as sa
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.notification_preference import NotificationChannel, NotificationPreference
from src.services.notification_preference_service import NOTIFICATION_TYPES

logger = logging.getLogger(__name__)

UNSUBSCRIBE_TOKEN_PURPOSE = "unsubscribe"
UNSUBSCRIBE_TOKEN_EXPIRE_DAYS = 30


def generate_unsubscribe_token(
    user_id: UUID,
    secret_key: str,
    algorithm: str = "HS256",
) -> str:
    """Create a signed JWT for one-click email unsubscribe.

    The token encodes the user_id and a purpose claim to distinguish
    it from authentication tokens. Valid for 30 days.

    Args:
        user_id: The user who will be unsubscribed when the token is used.
        secret_key: HMAC signing secret (same as app secret_key).
        algorithm: JWT signing algorithm, default HS256.

    Returns:
        Signed JWT string.
    """
    expiry = datetime.now(UTC) + timedelta(days=UNSUBSCRIBE_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "purpose": UNSUBSCRIBE_TOKEN_PURPOSE,
        "exp": expiry,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def validate_unsubscribe_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> UUID:
    """Decode and validate an unsubscribe JWT.

    Verifies signature, expiry, and purpose claim.

    Args:
        token: The signed JWT from the unsubscribe link.
        secret_key: HMAC signing secret.
        algorithm: JWT signing algorithm.

    Returns:
        The user_id encoded in the token.

    Raises:
        ValueError: If the token is invalid, expired, or has wrong purpose.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired unsubscribe token") from exc

    purpose = payload.get("purpose")
    if purpose != UNSUBSCRIBE_TOKEN_PURPOSE:
        raise ValueError("Token purpose is not 'unsubscribe'")

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token missing subject claim")

    try:
        return UUID(sub)
    except ValueError as exc:
        raise ValueError("Token subject is not a valid UUID") from exc


async def unsubscribe_all_email(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    """Disable all email notification preferences for a user.

    Upserts a disabled preference for every notification type on the
    email channel. Existing rows are updated; missing rows are inserted.

    Args:
        db: Async database session.
        user_id: The user whose email notifications will be disabled.

    Returns:
        Number of email preference rows affected.
    """
    now = datetime.now(UTC)
    count = 0

    for ntype in NOTIFICATION_TYPES:
        stmt = sa.select(NotificationPreference).where(
            NotificationPreference.user_id == user_id,
            NotificationPreference.notification_type == ntype,
            NotificationPreference.channel == NotificationChannel.EMAIL,
        )
        result = await db.execute(stmt)
        pref = result.scalar_one_or_none()

        if pref is not None:
            pref.enabled = False
            pref.updated_at = now
        else:
            pref = NotificationPreference(
                user_id=user_id,
                notification_type=ntype,
                channel=NotificationChannel.EMAIL,
                enabled=False,
                updated_at=now,
            )
            db.add(pref)

        count += 1

    await db.flush()
    logger.info(
        "Unsubscribed user_id=%s from all email notifications (%d types)",
        user_id,
        count,
    )
    return count
