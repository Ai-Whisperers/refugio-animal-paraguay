"""Referral tracking service — attribution of shares to conversions.

Tracks which user's share led to a donation, adoption application, or
registration. Provides referrer leaderboards and conversion metrics.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.referral import Referral, ReferralConversionType

logger = logging.getLogger(__name__)

# Configuration
REFERRAL_EXPIRY_DAYS = 30
LEADERBOARD_LIMIT = 10

VALID_CONVERSION_TYPES = frozenset({t.value for t in ReferralConversionType})


class ReferralError(Exception):
    """Base error for referral operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ReferralNotFoundError(ReferralError):
    """Raised when referral not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Referral not found",
            details=f"No referral found for: {identifier}",
        )


class InvalidConversionTypeError(ReferralError):
    """Raised for invalid conversion type."""

    def __init__(self, conversion_type: str) -> None:
        super().__init__(
            message="Invalid conversion type",
            details=f"Must be one of: {', '.join(sorted(VALID_CONVERSION_TYPES))}",
        )


class ReferralExpiredError(ReferralError):
    """Raised when referral has expired."""

    def __init__(self, referral_id: str) -> None:
        super().__init__(
            message="Referral expired",
            details=f"Referral {referral_id} has passed the {REFERRAL_EXPIRY_DAYS}-day window",
        )


class SelfReferralError(ReferralError):
    """Raised when user tries to refer themselves."""

    def __init__(self) -> None:
        super().__init__(
            message="Self-referral not allowed",
            details="A user cannot be their own referrer",
        )


def validate_conversion_type(conversion_type: str) -> None:
    """Validate conversion type."""
    if conversion_type not in VALID_CONVERSION_TYPES:
        raise InvalidConversionTypeError(conversion_type)


async def create_referral(
    *,
    referrer_user_id: UUID,
    landing_path: str | None = None,
    ip_address: str | None = None,
    db: AsyncSession,
) -> Referral:
    """Create a new referral tracking record when a user lands via a ref link.

    The referral starts unconverted and expires after REFERRAL_EXPIRY_DAYS.
    """
    now = datetime.now(UTC)
    referral = Referral(
        referrer_user_id=referrer_user_id,
        landing_path=landing_path,
        ip_address=ip_address,
        expires_at=now + timedelta(days=REFERRAL_EXPIRY_DAYS),
    )

    db.add(referral)
    await db.flush()

    logger.info(
        "Referral created: referrer=%s path=%s",
        referrer_user_id,
        landing_path,
    )
    return referral


async def convert_referral(
    *,
    referral_id: UUID,
    referred_user_id: UUID,
    conversion_type: str,
    conversion_entity_id: UUID | None = None,
    db: AsyncSession,
) -> Referral:
    """Mark a referral as converted (donation, adoption application, etc).

    Raises:
        ReferralNotFoundError: If referral not found.
        ReferralExpiredError: If referral has expired.
        SelfReferralError: If referred user is the referrer.
        InvalidConversionTypeError: If conversion type is invalid.
    """
    validate_conversion_type(conversion_type)

    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if referral is None:
        raise ReferralNotFoundError(str(referral_id))

    # Check expiry
    now = datetime.now(UTC)
    if now > referral.expires_at:
        raise ReferralExpiredError(str(referral_id))

    # Prevent self-referral
    if referred_user_id == referral.referrer_user_id:
        raise SelfReferralError()

    referral.referred_user_id = referred_user_id
    referral.conversion_type = conversion_type
    referral.conversion_entity_id = conversion_entity_id
    referral.converted_at = now

    await db.flush()

    logger.info(
        "Referral converted: id=%s type=%s referrer=%s referred=%s",
        referral_id,
        conversion_type,
        referral.referrer_user_id,
        referred_user_id,
    )
    return referral


async def get_referral_metrics(
    db: AsyncSession,
    *,
    days: int = REFERRAL_EXPIRY_DAYS,
) -> dict:
    """Get overall referral metrics.

    Returns total referrers, conversions by type, and conversion rate.
    """
    since = datetime.now(UTC) - timedelta(days=days)

    # Total referrals created
    total_result = await db.execute(
        select(func.count(Referral.id)).where(Referral.created_at >= since)
    )
    total_referrals = total_result.scalar_one()

    # Unique referrers
    referrers_result = await db.execute(
        select(func.count(func.distinct(Referral.referrer_user_id))).where(
            Referral.created_at >= since
        )
    )
    total_referrers = referrers_result.scalar_one()

    # Conversions by type
    conversions_result = await db.execute(
        select(Referral.conversion_type, func.count(Referral.id))
        .where(
            Referral.created_at >= since,
            Referral.converted_at.isnot(None),
        )
        .group_by(Referral.conversion_type)
    )
    conversions_by_type = {row[0]: row[1] for row in conversions_result.all()}

    # Total conversions
    total_conversions = sum(conversions_by_type.values())

    # Conversion rate
    conversion_rate = (
        round(total_conversions / total_referrals * 100, 1)
        if total_referrals > 0
        else 0.0
    )

    return {
        "total_referrals": total_referrals,
        "total_referrers": total_referrers,
        "total_conversions": total_conversions,
        "conversions_by_type": conversions_by_type,
        "conversion_rate_pct": conversion_rate,
        "period_days": days,
    }


async def get_referrer_leaderboard(
    db: AsyncSession,
    *,
    days: int = REFERRAL_EXPIRY_DAYS,
    limit: int = LEADERBOARD_LIMIT,
) -> list[dict]:
    """Get top referrers ranked by conversion count.

    Returns list of {referrer_user_id, total_referrals, total_conversions,
    conversions_by_type} dicts.
    """
    since = datetime.now(UTC) - timedelta(days=days)

    # Top referrers by conversion count
    result = await db.execute(
        select(
            Referral.referrer_user_id,
            func.count(Referral.id).label("total_referrals"),
            func.count(Referral.converted_at).label("total_conversions"),
        )
        .where(Referral.created_at >= since)
        .group_by(Referral.referrer_user_id)
        .order_by(func.count(Referral.converted_at).desc())
        .limit(limit)
    )

    items = []
    for row in result.all():
        # Get conversion breakdown for this referrer
        breakdown_result = await db.execute(
            select(Referral.conversion_type, func.count(Referral.id))
            .where(
                Referral.referrer_user_id == row[0],
                Referral.created_at >= since,
                Referral.converted_at.isnot(None),
            )
            .group_by(Referral.conversion_type)
        )
        conversions_by_type = {b_row[0]: b_row[1] for b_row in breakdown_result.all()}

        items.append(
            {
                "referrer_user_id": str(row[0]),
                "total_referrals": row[1],
                "total_conversions": row[2],
                "conversions_by_type": conversions_by_type,
            }
        )

    return items


async def get_referral_analytics(
    db: AsyncSession,
    *,
    days: int = REFERRAL_EXPIRY_DAYS,
) -> dict:
    """Get referral analytics time series.

    Returns daily referrals and conversions for the specified period.
    """
    since = datetime.now(UTC) - timedelta(days=days)

    # Daily referrals
    daily_result = await db.execute(
        select(
            func.date_trunc("day", Referral.created_at).label("day"),
            func.count(Referral.id).label("referrals"),
            func.count(Referral.converted_at).label("conversions"),
        )
        .where(Referral.created_at >= since)
        .group_by("day")
        .order_by("day")
    )

    daily_data = [
        {
            "date": str(row[0].date()) if row[0] else None,
            "referrals": row[1],
            "conversions": row[2],
        }
        for row in daily_result.all()
    ]

    return {
        "daily_data": daily_data,
        "period_days": days,
    }
