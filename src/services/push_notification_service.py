"""Push notification service for donors.

Manages Web Push subscriptions and sends push notifications to donors
for emergency cases, campaign updates, and donation confirmations.

Uses the Web Push protocol (RFC 8030) with VAPID authentication.
Actual push delivery is handled by the browser's push service endpoint.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)

# Configuration
MAX_FAILURE_COUNT = 5
DEFAULT_BATCH_SIZE = 100

# Push notification categories
VALID_PUSH_CATEGORIES = frozenset(
    {
        "emergency_created",
        "emergency_update",
        "campaign_milestone",
        "donation_confirmation",
        "campaign_completed",
    }
)

TITLE_MAX_LENGTH = 120
BODY_MAX_LENGTH = 500


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PushNotificationError(Exception):
    """Base error for push notification operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class SubscriptionNotFoundError(PushNotificationError):
    """Raised when push subscription not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Push subscription not found",
            details=f"No subscription found for: {identifier}",
        )


class InvalidPushCategoryError(PushNotificationError):
    """Raised for invalid push notification category."""

    def __init__(self, category: str) -> None:
        super().__init__(
            message="Invalid push category",
            details=f"Must be one of: {', '.join(sorted(VALID_PUSH_CATEGORIES))}. Got: {category}",
        )


class DuplicateSubscriptionError(PushNotificationError):
    """Raised when subscription already exists for donor+endpoint."""

    def __init__(self, donor_id: UUID) -> None:
        super().__init__(
            message="Duplicate subscription",
            details=f"Subscription already exists for donor {donor_id} at this endpoint",
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_push_category(category: str) -> None:
    """Validate that a push notification category is recognized."""
    if category not in VALID_PUSH_CATEGORIES:
        raise InvalidPushCategoryError(category)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def create_subscription(
    *,
    donor_id: UUID,
    endpoint: str,
    p256dh_key: str,
    auth_key: str,
    user_agent: str | None = None,
    db: AsyncSession,
) -> PushSubscription:
    """Create or reactivate a push subscription for a donor.

    If a subscription with the same donor+endpoint already exists and
    is inactive, it is reactivated with updated keys.

    Raises:
        PushNotificationError: If subscription data is invalid.
        DuplicateSubscriptionError: If active subscription already exists.
    """
    if not endpoint or not endpoint.startswith("https://"):
        raise PushNotificationError(
            "Invalid endpoint",
            details="Push endpoint must be a valid HTTPS URL",
        )
    if not p256dh_key:
        raise PushNotificationError(
            "Missing p256dh key",
            details="The p256dh encryption key is required",
        )
    if not auth_key:
        raise PushNotificationError(
            "Missing auth key",
            details="The auth secret is required",
        )

    # Check for existing subscription at this endpoint
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.donor_id == donor_id,
            PushSubscription.endpoint == endpoint,
        )
    )
    existing = result.scalar_one_or_none()

    if existing is not None:
        if existing.is_active:
            raise DuplicateSubscriptionError(donor_id)
        # Reactivate with updated keys
        existing.p256dh_key = p256dh_key
        existing.auth_key = auth_key
        existing.user_agent = user_agent
        existing.is_active = True
        existing.failure_count = 0
        await db.flush()
        logger.info(
            "Reactivated push subscription: id=%s donor=%s",
            existing.id,
            donor_id,
        )
        return existing

    subscription = PushSubscription(
        donor_id=donor_id,
        endpoint=endpoint,
        p256dh_key=p256dh_key,
        auth_key=auth_key,
        user_agent=user_agent,
    )
    db.add(subscription)
    await db.flush()

    logger.info(
        "Created push subscription: id=%s donor=%s",
        subscription.id,
        donor_id,
    )
    return subscription


async def deactivate_subscription(
    *,
    subscription_id: UUID,
    donor_id: UUID,
    db: AsyncSession,
) -> PushSubscription:
    """Deactivate a push subscription (unsubscribe).

    Raises:
        SubscriptionNotFoundError: If subscription not found or not owned by donor.
    """
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.id == subscription_id,
            PushSubscription.donor_id == donor_id,
        )
    )
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise SubscriptionNotFoundError(str(subscription_id))

    subscription.is_active = False
    await db.flush()

    logger.info(
        "Deactivated push subscription: id=%s donor=%s",
        subscription_id,
        donor_id,
    )
    return subscription


async def get_donor_subscriptions(
    donor_id: UUID,
    db: AsyncSession,
    *,
    active_only: bool = True,
) -> list[PushSubscription]:
    """List push subscriptions for a donor."""
    stmt = select(PushSubscription).where(
        PushSubscription.donor_id == donor_id,
    )
    if active_only:
        stmt = stmt.where(PushSubscription.is_active.is_(True))

    stmt = stmt.order_by(PushSubscription.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_active_subscriptions_batch(
    db: AsyncSession,
    *,
    offset: int = 0,
    limit: int = DEFAULT_BATCH_SIZE,
) -> list[PushSubscription]:
    """Get a batch of active subscriptions for bulk push sending.

    Excludes subscriptions that have exceeded the failure threshold.
    """
    stmt = (
        select(PushSubscription)
        .where(
            PushSubscription.is_active.is_(True),
            PushSubscription.failure_count < MAX_FAILURE_COUNT,
        )
        .order_by(PushSubscription.created_at)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def record_push_result(
    *,
    subscription_id: UUID,
    success: bool,
    db: AsyncSession,
) -> None:
    """Record the result of a push delivery attempt.

    On success: reset failure count, update last_used_at.
    On failure: increment failure count, deactivate if threshold exceeded.
    """
    if success:
        await db.execute(
            update(PushSubscription)
            .where(PushSubscription.id == subscription_id)
            .values(
                failure_count=0,
                last_used_at=datetime.now(UTC),
            )
        )
    else:
        await db.execute(
            update(PushSubscription)
            .where(PushSubscription.id == subscription_id)
            .values(
                failure_count=PushSubscription.failure_count + 1,
            )
        )
        # Check if we should deactivate
        result = await db.execute(
            select(PushSubscription).where(PushSubscription.id == subscription_id)
        )
        sub = result.scalar_one_or_none()
        if sub and sub.failure_count >= MAX_FAILURE_COUNT:
            sub.is_active = False
            logger.warning(
                "Deactivated subscription after %d failures: id=%s",
                MAX_FAILURE_COUNT,
                subscription_id,
            )

    await db.flush()


async def prepare_push_payload(
    *,
    category: str,
    title: str,
    body: str,
    url: str | None = None,
    data: dict | None = None,
) -> dict:
    """Prepare a push notification payload.

    Validates the category and constructs the notification payload
    ready for Web Push delivery.

    Raises:
        InvalidPushCategoryError: If category is not valid.
        PushNotificationError: If title or body exceeds length limits.
    """
    validate_push_category(category)

    if len(title) > TITLE_MAX_LENGTH:
        raise PushNotificationError(
            "Title too long",
            details=f"Title must be at most {TITLE_MAX_LENGTH} characters",
        )
    if len(body) > BODY_MAX_LENGTH:
        raise PushNotificationError(
            "Body too long",
            details=f"Body must be at most {BODY_MAX_LENGTH} characters",
        )

    payload: dict = {
        "category": category,
        "title": title,
        "body": body,
    }
    if url:
        payload["url"] = url
    if data:
        payload["data"] = data

    return payload


async def get_push_stats(db: AsyncSession) -> dict:
    """Get push notification subscription statistics.

    Returns:
        Dict with total_subscriptions, active_subscriptions, and
        subscriptions_by_failure_count.
    """
    total_result = await db.execute(select(func.count()).select_from(PushSubscription))
    total = total_result.scalar_one()

    active_result = await db.execute(
        select(func.count())
        .select_from(PushSubscription)
        .where(PushSubscription.is_active.is_(True))
    )
    active = active_result.scalar_one()

    failed_result = await db.execute(
        select(func.count())
        .select_from(PushSubscription)
        .where(
            PushSubscription.is_active.is_(True),
            PushSubscription.failure_count > 0,
        )
    )
    with_failures = failed_result.scalar_one()

    return {
        "total_subscriptions": total,
        "active_subscriptions": active,
        "inactive_subscriptions": total - active,
        "active_with_failures": with_failures,
    }
