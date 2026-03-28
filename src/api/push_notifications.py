"""Push notification API endpoints.

Donors can subscribe/unsubscribe from push notifications.
Staff can view subscription stats and trigger push notifications.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.session import get_async_session
from src.services.push_notification_service import (
    DuplicateSubscriptionError,
    InvalidPushCategoryError,
    PushNotificationError,
    SubscriptionNotFoundError,
    create_subscription,
    deactivate_subscription,
    get_donor_subscriptions,
    get_push_stats,
    prepare_push_payload,
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class PushSubscribeRequest(BaseModel):
    """Request body for creating a push subscription."""

    donor_id: UUID
    endpoint: str = Field(..., min_length=1)
    p256dh_key: str = Field(..., min_length=1)
    auth_key: str = Field(..., min_length=1)
    user_agent: str | None = None


class PushUnsubscribeRequest(BaseModel):
    """Request body for deactivating a push subscription."""

    donor_id: UUID


class PushSubscriptionResponse(BaseModel):
    """Push subscription response."""

    id: UUID
    donor_id: UUID
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: str | None = None
    is_active: bool
    failure_count: int
    last_used_at: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


class PushSendRequest(BaseModel):
    """Request body for sending a push notification."""

    category: str
    title: str = Field(..., max_length=120)
    body: str = Field(..., max_length=500)
    url: str | None = None
    data: dict | None = None


class PushPayloadResponse(BaseModel):
    """Response after preparing a push payload."""

    category: str
    title: str
    body: str
    url: str | None = None
    data: dict | None = None
    target_subscriptions: int


class PushStatsResponse(BaseModel):
    """Push subscription statistics."""

    total_subscriptions: int
    active_subscriptions: int
    inactive_subscriptions: int
    active_with_failures: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialise_subscription(sub: object) -> dict:
    """Convert a PushSubscription ORM object to a response dict."""
    last_used = getattr(sub, "last_used_at", None)
    return {
        "id": sub.id,  # type: ignore[attr-defined]
        "donor_id": sub.donor_id,  # type: ignore[attr-defined]
        "endpoint": sub.endpoint,  # type: ignore[attr-defined]
        "p256dh_key": sub.p256dh_key,  # type: ignore[attr-defined]
        "auth_key": sub.auth_key,  # type: ignore[attr-defined]
        "user_agent": sub.user_agent,  # type: ignore[attr-defined]
        "is_active": sub.is_active,  # type: ignore[attr-defined]
        "failure_count": sub.failure_count,  # type: ignore[attr-defined]
        "last_used_at": last_used.isoformat() if last_used else None,
        "created_at": sub.created_at.isoformat(),  # type: ignore[attr-defined]
    }


def _handle_push_error(exc: Exception) -> None:
    """Map service-layer exceptions to HTTP responses."""
    if isinstance(exc, SubscriptionNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, DuplicateSubscriptionError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, InvalidPushCategoryError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None
    if isinstance(exc, PushNotificationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": exc.message, "details": exc.details},
        ) from None


# ---------------------------------------------------------------------------
# Public router (donor-facing)
# ---------------------------------------------------------------------------

public_router = APIRouter(
    prefix="/api/push",
    tags=["push-notifications"],
)


@public_router.post(
    "/subscribe",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe(
    body: PushSubscribeRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Subscribe a donor to push notifications."""
    try:
        sub = await create_subscription(
            donor_id=body.donor_id,
            endpoint=body.endpoint,
            p256dh_key=body.p256dh_key,
            auth_key=body.auth_key,
            user_agent=body.user_agent,
            db=db,
        )
        await db.commit()
        return _serialise_subscription(sub)
    except Exception as exc:
        _handle_push_error(exc)
        raise


@public_router.delete(
    "/subscribe/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unsubscribe(
    subscription_id: UUID,
    body: PushUnsubscribeRequest,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Unsubscribe (deactivate) a push subscription."""
    try:
        await deactivate_subscription(
            subscription_id=subscription_id,
            donor_id=body.donor_id,
            db=db,
        )
        await db.commit()
    except Exception as exc:
        _handle_push_error(exc)
        raise


@public_router.get(
    "/subscriptions/{donor_id}",
    response_model=list[PushSubscriptionResponse],
)
async def list_subscriptions(
    donor_id: UUID,
    db: AsyncSession = Depends(get_async_session),
) -> list[dict]:
    """List active push subscriptions for a donor."""
    subs = await get_donor_subscriptions(donor_id, db)
    return [_serialise_subscription(s) for s in subs]


# ---------------------------------------------------------------------------
# Admin router (staff-facing)
# ---------------------------------------------------------------------------

admin_router = APIRouter(
    prefix="/api/admin/push",
    tags=["push-notifications-admin"],
    dependencies=[Depends(require_staff)],
)


@admin_router.get("/stats", response_model=PushStatsResponse)
async def subscription_stats(
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Get push subscription statistics."""
    return await get_push_stats(db)


@admin_router.post("/send", response_model=PushPayloadResponse)
async def send_push(
    body: PushSendRequest,
    db: AsyncSession = Depends(get_async_session),
) -> dict:
    """Prepare and queue a push notification for all active subscribers.

    Returns the prepared payload and target subscription count.
    Actual delivery is handled asynchronously via the push service.
    """
    try:
        payload = await prepare_push_payload(
            category=body.category,
            title=body.title,
            body=body.body,
            url=body.url,
            data=body.data,
        )
        # Count target subscriptions
        stats = await get_push_stats(db)

        return {
            **payload,
            "target_subscriptions": stats["active_subscriptions"],
        }
    except Exception as exc:
        _handle_push_error(exc)
        raise
