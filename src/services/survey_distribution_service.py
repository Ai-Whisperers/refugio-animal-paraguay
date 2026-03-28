"""Service layer for survey distribution.

Handles sending surveys via email and WhatsApp, tracking delivery status.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.survey_distribution import (
    VALID_CHANNELS,
    VALID_DELIVERY_STATUSES,
    DeliveryStatus,
    SurveyDistribution,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class DistributionError(Exception):
    """Base error for distribution operations."""


class DistributionNotFoundError(DistributionError):
    """Raised when a distribution record does not exist."""


class InvalidDistributionError(DistributionError):
    """Raised when distribution validation fails."""


async def create_distribution(
    db: AsyncSession,
    survey_id: UUID,
    channel: str,
    sent_by: UUID,
    recipient_email: str | None = None,
    recipient_phone: str | None = None,
) -> dict:
    """Create a survey distribution record."""
    if channel not in VALID_CHANNELS:
        raise InvalidDistributionError(
            f"Invalid channel '{channel}', must be one of {VALID_CHANNELS}"
        )

    if channel == "email" and not recipient_email:
        raise InvalidDistributionError("Email channel requires recipient_email")
    if channel == "whatsapp" and not recipient_phone:
        raise InvalidDistributionError("WhatsApp channel requires recipient_phone")

    distribution = SurveyDistribution(
        survey_id=survey_id,
        channel=channel,
        recipient_email=recipient_email,
        recipient_phone=recipient_phone,
        delivery_status=DeliveryStatus.PENDING.value,
        sent_by=sent_by,
    )
    db.add(distribution)
    await db.flush()
    await db.refresh(distribution)

    return _distribution_to_dict(distribution)


async def create_bulk_distribution(
    db: AsyncSession,
    survey_id: UUID,
    channel: str,
    sent_by: UUID,
    recipients: list[dict],
) -> list[dict]:
    """Create multiple distribution records at once.

    Each recipient dict should have 'email' and/or 'phone' keys.
    """
    if channel not in VALID_CHANNELS:
        raise InvalidDistributionError(
            f"Invalid channel '{channel}', must be one of {VALID_CHANNELS}"
        )

    if not recipients:
        raise InvalidDistributionError("At least one recipient is required")

    results = []
    for recipient in recipients:
        email = recipient.get("email")
        phone = recipient.get("phone")

        if channel == "email" and not email:
            raise InvalidDistributionError("Email channel requires email for each recipient")
        if channel == "whatsapp" and not phone:
            raise InvalidDistributionError("WhatsApp channel requires phone for each recipient")

        dist = SurveyDistribution(
            survey_id=survey_id,
            channel=channel,
            recipient_email=email,
            recipient_phone=phone,
            delivery_status=DeliveryStatus.PENDING.value,
            sent_by=sent_by,
        )
        db.add(dist)
        await db.flush()
        await db.refresh(dist)
        results.append(_distribution_to_dict(dist))

    return results


async def get_distribution(db: AsyncSession, distribution_id: UUID) -> dict:
    """Get a distribution record by ID."""
    result = await db.execute(
        select(SurveyDistribution).where(SurveyDistribution.id == distribution_id)
    )
    distribution = result.scalar_one_or_none()
    if distribution is None:
        raise DistributionNotFoundError(f"Distribution {distribution_id} not found")
    return _distribution_to_dict(distribution)


async def list_distributions(
    db: AsyncSession,
    survey_id: UUID | None = None,
    channel: str | None = None,
    status_filter: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict:
    """List distribution records with optional filters."""
    base_query = select(SurveyDistribution)

    if survey_id is not None:
        base_query = base_query.where(SurveyDistribution.survey_id == survey_id)
    if channel is not None:
        base_query = base_query.where(SurveyDistribution.channel == channel)
    if status_filter is not None:
        base_query = base_query.where(SurveyDistribution.delivery_status == status_filter)

    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(SurveyDistribution.created_at.desc()).limit(limit).offset(offset)
    )
    distributions = list(result.scalars().all())

    return {
        "distributions": [_distribution_to_dict(d) for d in distributions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def update_delivery_status(
    db: AsyncSession,
    distribution_id: UUID,
    new_status: str,
    failure_reason: str | None = None,
) -> dict:
    """Update the delivery status of a distribution."""
    result = await db.execute(
        select(SurveyDistribution).where(SurveyDistribution.id == distribution_id)
    )
    distribution = result.scalar_one_or_none()
    if distribution is None:
        raise DistributionNotFoundError(f"Distribution {distribution_id} not found")

    if new_status not in VALID_DELIVERY_STATUSES:
        raise InvalidDistributionError(f"Invalid delivery status '{new_status}'")

    distribution.delivery_status = new_status

    now = datetime.now(UTC)
    if new_status == DeliveryStatus.SENT:
        distribution.sent_at = now
    elif new_status == DeliveryStatus.DELIVERED:
        distribution.delivered_at = now
    elif new_status == DeliveryStatus.FAILED and failure_reason:
        distribution.failure_reason = failure_reason

    await db.flush()
    await db.refresh(distribution)

    return _distribution_to_dict(distribution)


async def get_distribution_stats(db: AsyncSession, survey_id: UUID) -> dict:
    """Get distribution statistics for a survey."""
    base_query = select(SurveyDistribution).where(SurveyDistribution.survey_id == survey_id)

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar_one()

    stats: dict[str, int] = {}
    for status_val in VALID_DELIVERY_STATUSES:
        status_query = base_query.where(SurveyDistribution.delivery_status == status_val)
        count_result = await db.execute(select(func.count()).select_from(status_query.subquery()))
        stats[status_val] = count_result.scalar_one()

    return {
        "survey_id": survey_id,
        "total": total,
        "by_status": stats,
    }


def _distribution_to_dict(distribution: SurveyDistribution) -> dict:
    """Convert a SurveyDistribution to a dict."""
    return {
        "id": distribution.id,
        "survey_id": distribution.survey_id,
        "channel": distribution.channel,
        "recipient_email": distribution.recipient_email,
        "recipient_phone": distribution.recipient_phone,
        "delivery_status": distribution.delivery_status,
        "sent_at": distribution.sent_at,
        "delivered_at": distribution.delivered_at,
        "failure_reason": distribution.failure_reason,
        "sent_by": distribution.sent_by,
        "created_at": distribution.created_at,
    }
