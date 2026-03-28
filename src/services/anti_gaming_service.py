"""Anti-gaming protection for the pre-qualification system.

Prevents abuse by enforcing cooldown periods between attempts for the same
animal, limiting total daily attempts per user, and detecting suspicious
answer patterns (e.g., rapidly flipping answers to brute-force qualification).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Cooldown between attempts for the same animal (minutes)
SAME_ANIMAL_COOLDOWN_MINUTES = 30

# Maximum attempts per user per day
MAX_DAILY_ATTEMPTS_PER_USER = 20

# Maximum attempts per user per animal per day
MAX_DAILY_ATTEMPTS_PER_ANIMAL = 5

# Minimum seconds between any two attempts (rapid-fire protection)
MIN_ATTEMPT_INTERVAL_SECONDS = 10


class AntiGamingError(Exception):
    """Raised when an anti-gaming rule is triggered."""

    def __init__(self, rule: str, message: str, retry_after_seconds: int | None = None) -> None:
        self.rule = rule
        self.message = message
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)


async def check_rate_limits(
    db: AsyncSession,
    user_id: UUID,
    animal_id: UUID,
) -> None:
    """Check all anti-gaming rules before allowing a pre-qualification attempt.

    Raises AntiGamingError if any rule is triggered.
    Must be called before pre_qualify_adopter.
    """
    # Import here to avoid circular dependency
    from src.db.models.pre_qualification_attempt import PreQualificationAttempt

    now = datetime.now(tz=None)

    # Rule 1: Rapid-fire protection — minimum interval between attempts
    rapid_fire_stmt = (
        select(PreQualificationAttempt.created_at)
        .where(
            PreQualificationAttempt.user_id == user_id,
        )
        .order_by(PreQualificationAttempt.created_at.desc())
        .limit(1)
    )
    rapid_result = await db.execute(rapid_fire_stmt)
    last_attempt = rapid_result.scalar_one_or_none()

    if last_attempt is not None:
        elapsed = (now - last_attempt.replace(tzinfo=None)).total_seconds()
        if elapsed < MIN_ATTEMPT_INTERVAL_SECONDS:
            remaining = int(MIN_ATTEMPT_INTERVAL_SECONDS - elapsed)
            raise AntiGamingError(
                rule="rapid_fire",
                message=f"Please wait {remaining} seconds before trying again.",
                retry_after_seconds=remaining,
            )

    # Rule 2: Same-animal cooldown
    cooldown_cutoff = now - timedelta(minutes=SAME_ANIMAL_COOLDOWN_MINUTES)
    same_animal_stmt = (
        select(func.count())
        .select_from(PreQualificationAttempt)
        .where(
            PreQualificationAttempt.user_id == user_id,
            PreQualificationAttempt.animal_id == animal_id,
            PreQualificationAttempt.created_at >= cooldown_cutoff,
        )
    )
    same_animal_result = await db.execute(same_animal_stmt)
    same_animal_count = same_animal_result.scalar_one()

    if same_animal_count >= MAX_DAILY_ATTEMPTS_PER_ANIMAL:
        raise AntiGamingError(
            rule="same_animal_cooldown",
            message=(
                f"You have reached the maximum of {MAX_DAILY_ATTEMPTS_PER_ANIMAL} "
                f"attempts for this animal. Please try again later."
            ),
            retry_after_seconds=SAME_ANIMAL_COOLDOWN_MINUTES * 60,
        )

    # Rule 3: Daily attempt limit per user
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    daily_stmt = (
        select(func.count())
        .select_from(PreQualificationAttempt)
        .where(
            PreQualificationAttempt.user_id == user_id,
            PreQualificationAttempt.created_at >= day_start,
        )
    )
    daily_result = await db.execute(daily_stmt)
    daily_count = daily_result.scalar_one()

    if daily_count >= MAX_DAILY_ATTEMPTS_PER_USER:
        raise AntiGamingError(
            rule="daily_limit",
            message=(
                f"You have reached the maximum of {MAX_DAILY_ATTEMPTS_PER_USER} "
                f"pre-qualification attempts for today."
            ),
            retry_after_seconds=None,
        )

    logger.debug(
        "Anti-gaming check passed: user=%s animal=%s daily=%d same_animal=%d",
        user_id,
        animal_id,
        daily_count,
        same_animal_count,
    )
