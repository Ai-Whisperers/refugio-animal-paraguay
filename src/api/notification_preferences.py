"""Notification preferences router.

Endpoints for viewing and updating notification delivery preferences.
Users control which notification types they receive through each channel.

Endpoints:
    GET  /notification-preferences — list all preferences (with defaults)
    PUT  /notification-preferences — bulk update preferences
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.schemas.notification_preference import (
    PreferenceBulkUpdate,
    PreferenceListResponse,
    PreferenceResponse,
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
