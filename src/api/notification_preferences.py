"""Notification preferences router.

Endpoints for viewing and updating notification delivery preferences.
Users control which notification types they receive through each channel,
at what delivery frequency, and can unsubscribe from email without login.

Endpoints:
    GET  /notification-preferences                   -- list all preferences (with defaults)
    PUT  /notification-preferences                   -- bulk update preferences
    GET  /notification-preferences/unsubscribe-link  -- generate signed unsubscribe URL
    GET  /notification-preferences/unsubscribe       -- process unsubscribe (public, token-based)
    GET  /notification-preferences/frequency         -- get per-channel frequency settings
    PUT  /notification-preferences/frequency         -- update per-channel frequency settings
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.config import Settings
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.schemas.notification_preference import (
    FrequencyBulkUpdate,
    FrequencyListResponse,
    FrequencyResponse,
    PreferenceBulkUpdate,
    PreferenceListResponse,
    PreferenceResponse,
    UnsubscribeLinkResponse,
    UnsubscribeResult,
)
from src.services.email_unsubscribe_service import (
    UNSUBSCRIBE_TOKEN_EXPIRE_DAYS,
    generate_unsubscribe_token,
    unsubscribe_all_email,
    validate_unsubscribe_token,
)
from src.services.notification_frequency_service import (
    get_channel_frequencies,
    set_channel_frequency,
)
from src.services.notification_preference_service import (
    get_preferences_with_defaults,
    update_preferences,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notification-preferences",
    tags=["notification-preferences"],
    responses=AUTHENTICATED_RESPONSES,
)


@router.get("", response_model=PreferenceListResponse)
async def list_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> PreferenceListResponse:
    """List all notification preferences for the current user.

    Returns the full matrix of notification_type x channel, filling
    in defaults (enabled=True) for any missing combinations.
    """
    prefs = await get_preferences_with_defaults(db, current_user.id)
    return PreferenceListResponse(
        preferences=[PreferenceResponse(**p) for p in prefs],
    )


@router.put("", response_model=PreferenceListResponse)
async def update_user_preferences(
    payload: PreferenceBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> PreferenceListResponse:
    """Bulk update notification preferences for the current user.

    Accepts a list of (notification_type, channel, enabled) triples.
    Existing preferences are updated; missing ones are created.
    Returns the full updated preference matrix.
    """
    updates = [p.model_dump() for p in payload.preferences]
    await update_preferences(db, current_user.id, updates)

    # Return full matrix after update
    prefs = await get_preferences_with_defaults(db, current_user.id)
    return PreferenceListResponse(
        preferences=[PreferenceResponse(**p) for p in prefs],
    )


@router.get("/unsubscribe-link", response_model=UnsubscribeLinkResponse)
async def get_unsubscribe_link(
    request: Request,
    current_user: User = Depends(require_staff),
    settings: Settings = Depends(Settings),
) -> UnsubscribeLinkResponse:
    """Generate a signed one-click unsubscribe URL for the current user.

    The URL contains a signed JWT token valid for 30 days. Clicking the
    URL disables all email notification preferences without requiring login.

    Returns the full unsubscribe URL including the token query parameter.
    """
    token = generate_unsubscribe_token(
        current_user.id,
        settings.secret_key,
        settings.algorithm,
    )
    base_url = str(request.base_url).rstrip("/")
    unsubscribe_url = f"{base_url}/notification-preferences/unsubscribe?token={token}"
    return UnsubscribeLinkResponse(
        unsubscribe_url=unsubscribe_url,
        expires_in_days=UNSUBSCRIBE_TOKEN_EXPIRE_DAYS,
    )


@router.get(
    "/unsubscribe",
    response_model=UnsubscribeResult,
    responses={400: {"description": "Invalid or expired token"}},
)
async def process_unsubscribe(
    token: str = Query(..., description="Signed unsubscribe JWT from the unsubscribe link"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(Settings),
) -> UnsubscribeResult:
    """Process a one-click email unsubscribe request.

    Validates the signed token and disables all email notification
    preferences for the user encoded in the token. No authentication
    is required — the token itself proves intent.

    Returns a confirmation message with the number of preferences updated.
    """
    try:
        user_id = validate_unsubscribe_token(
            token,
            settings.secret_key,
            settings.algorithm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    count = await unsubscribe_all_email(db, user_id)
    await db.commit()

    logger.info("Email unsubscribe processed for user_id=%s (%d prefs)", user_id, count)
    return UnsubscribeResult(
        message="Successfully unsubscribed from all email notifications.",
        preferences_updated=count,
    )


@router.get("/frequency", response_model=FrequencyListResponse)
async def list_frequency_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> FrequencyListResponse:
    """Get notification delivery frequency settings for the current user.

    Returns frequency for each supported channel (in_app, email).
    Missing settings default to 'immediate'. Email supports batching
    via 'daily_digest' or 'weekly'; in_app is always immediate.
    """
    freqs = await get_channel_frequencies(db, current_user.id)
    return FrequencyListResponse(
        frequencies=[FrequencyResponse(**f) for f in freqs],
    )


@router.put("/frequency", response_model=FrequencyListResponse)
async def update_frequency_settings(
    payload: FrequencyBulkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> FrequencyListResponse:
    """Update notification delivery frequency for one or more channels.

    Accepts a list of (channel, frequency) pairs. Valid frequencies are:
    - immediate: notifications sent as they occur (default)
    - daily_digest: all notifications batched and sent once per day
    - weekly: all notifications batched and sent once per week

    Returns all channel frequency settings after the update.
    """
    for item in payload.frequencies:
        await set_channel_frequency(
            db,
            current_user.id,
            item.channel,
            item.frequency,
        )

    freqs = await get_channel_frequencies(db, current_user.id)
    return FrequencyListResponse(
        frequencies=[FrequencyResponse(**f) for f in freqs],
    )
