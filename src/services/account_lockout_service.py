"""Account lockout service: track failed login attempts and temporary lockout.

Locks an account for LOCKOUT_DURATION_MINUTES after MAX_FAILED_ATTEMPTS
consecutive failed logins. A successful login resets the counter.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def is_account_locked(user: User) -> bool:
    """Return True if the account is currently locked out."""
    if user.locked_until is None:
        return False
    return datetime.now(UTC) < user.locked_until


def lockout_remaining_seconds(user: User) -> int:
    """Return seconds remaining on the lockout, or 0 if not locked."""
    if user.locked_until is None:
        return 0
    remaining = (user.locked_until - datetime.now(UTC)).total_seconds()
    return max(0, int(remaining))


async def record_failed_attempt(db: AsyncSession, user: User) -> bool:
    """Increment the failed-attempt counter.

    Returns True if the account has just been locked (threshold reached).
    """
    user.failed_login_attempts += 1
    locked = False
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        locked = True
    await db.flush()
    return locked


async def reset_failed_attempts(db: AsyncSession, user: User) -> None:
    """Reset the counter and clear any lockout after a successful login."""
    if user.failed_login_attempts != 0 or user.locked_until is not None:
        user.failed_login_attempts = 0
        user.locked_until = None
        await db.flush()
