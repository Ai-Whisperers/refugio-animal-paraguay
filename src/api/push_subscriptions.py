"""Push notification subscription management API.

Manages browser push notification subscriptions for web push
notifications. Supports creating, listing, and deleting subscriptions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session

router = APIRouter(prefix="/api/push-subscriptions", tags=["push-notifications"])


# --- Schemas ---


class PushSubscriptionKeys(BaseModel):
    """Web Push subscription keys."""

    p256dh: str = Field(..., description="P-256 Diffie-Hellman public key")
    auth: str = Field(..., description="Authentication secret")


class PushSubscriptionCreate(BaseModel):
    """Create a new push subscription."""

    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: PushSubscriptionKeys


class PushSubscriptionDelete(BaseModel):
    """Delete a push subscription by endpoint."""

    endpoint: str = Field(..., description="Push service endpoint URL to remove")


class PushSubscriptionResponse(BaseModel):
    """Push subscription response."""

    id: str
    endpoint: str
    created_at: str


# --- Helpers ---


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# --- In-memory store (replace with DB model when persistence needed) ---
# Using a simple dict for MVP; production should use a DB table
_subscriptions: dict[str, dict[str, Any]] = {}


# --- Endpoints ---


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PushSubscriptionResponse,
)
async def create_push_subscription(
    payload: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Register a new push notification subscription."""
    subscription_id = str(uuid.uuid4())
    record = {
        "id": subscription_id,
        "endpoint": payload.endpoint,
        "p256dh": payload.keys.p256dh,
        "auth": payload.keys.auth,
        "created_at": _now_iso(),
    }
    _subscriptions[payload.endpoint] = record

    return {
        "id": subscription_id,
        "endpoint": payload.endpoint,
        "created_at": record["created_at"],
    }


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_push_subscription(
    payload: PushSubscriptionDelete,
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Remove a push notification subscription."""
    if payload.endpoint not in _subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    del _subscriptions[payload.endpoint]


@router.get("", response_model=list[PushSubscriptionResponse])
async def list_push_subscriptions(
    db: AsyncSession = Depends(get_async_session),
) -> list[dict[str, Any]]:
    """List all active push subscriptions (admin only in production)."""
    return [
        {
            "id": sub["id"],
            "endpoint": sub["endpoint"],
            "created_at": sub["created_at"],
        }
        for sub in _subscriptions.values()
    ]
