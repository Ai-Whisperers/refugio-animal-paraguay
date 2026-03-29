"""Admin security endpoints — JWT key rotation status.

Provides an endpoint for administrators to check the current state of JWT
key rotation: whether a previous key is configured and how long the rotation
window has been active.

The rotation procedure itself is performed via environment variables and a
controlled restart (see ``src/auth/utils.py`` for the full runbook).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.auth.dependencies import require_admin
from src.config import Settings, get_settings
from src.db.models.user import User

router = APIRouter(prefix="/admin/security", tags=["admin-security"])


class KeyRotationStatus(BaseModel):
    """Current state of JWT key rotation."""

    rotation_active: bool
    """True when SECRET_KEY_PREVIOUS is configured (rotation window is open)."""

    previous_key_configured: bool
    """Alias for rotation_active — explicit field for API clarity."""

    active_key_prefix: str
    """First 8 characters of the active key (masked) — for identifying which key is active."""

    previous_key_prefix: str
    """First 8 characters of the previous key (masked). Empty string when not set."""

    checked_at: datetime
    """UTC timestamp when this status was generated."""

    recommendation: str
    """Operational guidance based on current rotation state."""


@router.get(
    "/jwt-rotation-status",
    response_model=KeyRotationStatus,
    summary="JWT key rotation status",
    description=(
        "Returns the current JWT key rotation state. "
        "Shows whether a previous key is configured and provides operational guidance. "
        "Requires admin role."
    ),
)
async def get_jwt_rotation_status(
    _admin: User = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> KeyRotationStatus:
    """Return the current JWT signing key rotation status.

    Used by operations staff to verify rotation is progressing correctly
    and to know when it is safe to clear SECRET_KEY_PREVIOUS.
    """
    rotation_active = bool(settings.secret_key_previous)

    # Mask keys: show first 8 chars only — enough to identify which key is which.
    active_key_prefix = settings.secret_key[:8] + "..."
    previous_key_prefix = (settings.secret_key_previous[:8] + "...") if rotation_active else ""

    if rotation_active:
        recommendation = (
            f"Key rotation is in progress. Tokens signed with the previous key are still accepted. "
            f"Wait {settings.access_token_expire_minutes} minutes after starting rotation, "
            f"then clear SECRET_KEY_PREVIOUS and restart to complete rotation."
        )
    else:
        recommendation = (
            "No rotation in progress. To rotate the JWT secret: "
            "set SECRET_KEY_PREVIOUS=<current SECRET_KEY> and SECRET_KEY=<new value>, "
            "then restart the application."
        )

    return KeyRotationStatus(
        rotation_active=rotation_active,
        previous_key_configured=rotation_active,
        active_key_prefix=active_key_prefix,
        previous_key_prefix=previous_key_prefix,
        checked_at=datetime.now(UTC),
        recommendation=recommendation,
    )
