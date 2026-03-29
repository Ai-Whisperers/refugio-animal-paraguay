"""Backup code service for 2FA recovery.

Generates, hashes, and validates one-time backup codes that staff can use
to log in if they lose access to their authenticator app.

Each batch contains BACKUP_CODE_COUNT unique codes. Generating a new batch
deletes all previous codes for the user (used and unused alike). Codes are
presented to the user only once and stored as bcrypt hashes.

Format: 8 uppercase alphanumeric characters (e.g. "A3BX72KP") — easy to
read and type, hard to brute-force (36^8 ≈ 2.8 trillion combinations).
"""

import secrets
import string
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import hash_password, verify_password
from src.db.models.totp_backup_code import BACKUP_CODE_COUNT, TotpBackupCode

BACKUP_CODE_ALPHABET = string.ascii_uppercase + string.digits
BACKUP_CODE_LENGTH = 8


def _generate_raw_code() -> str:
    """Return a single random 8-character code using an unambiguous character set.

    Excludes easily confused characters (0/O, 1/I/L) for human readability.
    """
    safe_chars = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
    return "".join(secrets.choice(safe_chars) for _ in range(BACKUP_CODE_LENGTH))


async def generate_backup_codes(
    db: AsyncSession,
    user_id: object,
) -> list[str]:
    """Generate a fresh batch of backup codes for *user_id*.

    Deletes all existing codes (used or not) and inserts BACKUP_CODE_COUNT
    new hashed codes. Returns the plain-text codes — the caller must
    present these to the user immediately; they cannot be recovered later.

    Args:
        db:      Async database session (transaction must be managed by caller).
        user_id: UUID of the user who owns the codes.
    """
    # Delete all existing backup codes for this user
    await db.execute(delete(TotpBackupCode).where(TotpBackupCode.user_id == user_id))

    plain_codes = [_generate_raw_code() for _ in range(BACKUP_CODE_COUNT)]

    for plain in plain_codes:
        code_obj = TotpBackupCode(
            user_id=user_id,
            code_hash=hash_password(plain),
        )
        db.add(code_obj)

    await db.flush()
    return plain_codes


async def use_backup_code(
    db: AsyncSession,
    user_id: object,
    plain_code: str,
) -> bool:
    """Attempt to consume *plain_code* as a valid backup code for *user_id*.

    Returns True and marks the code as used if a match is found. Returns False
    if no matching unused code exists (invalid or already consumed).

    Args:
        db:         Async database session.
        user_id:    UUID of the authenticating user.
        plain_code: Raw backup code submitted during login.
    """
    clean = plain_code.strip().upper().replace("-", "").replace(" ", "")

    # Fetch all unused codes for the user
    result = await db.execute(
        select(TotpBackupCode).where(
            TotpBackupCode.user_id == user_id,
            TotpBackupCode.used_at.is_(None),
        )
    )
    rows = result.scalars().all()

    for row in rows:
        if verify_password(clean, row.code_hash):
            row.used_at = datetime.now(UTC)
            await db.flush()
            return True

    return False


async def count_remaining_backup_codes(
    db: AsyncSession,
    user_id: object,
) -> int:
    """Return the number of unused backup codes for *user_id*."""
    result = await db.execute(
        select(TotpBackupCode).where(
            TotpBackupCode.user_id == user_id,
            TotpBackupCode.used_at.is_(None),
        )
    )
    return len(result.scalars().all())


__all__ = [
    "BACKUP_CODE_COUNT",
    "BACKUP_CODE_LENGTH",
    "count_remaining_backup_codes",
    "generate_backup_codes",
    "use_backup_code",
]
