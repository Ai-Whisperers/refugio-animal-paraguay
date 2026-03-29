"""Two-Factor Authentication router.

Endpoints:
  GET  /auth/2fa/status   — Return whether 2FA is enabled for the current user
  POST /auth/2fa/setup    — Generate a new TOTP secret (does NOT activate 2FA yet)
  POST /auth/2fa/verify   — Confirm the first TOTP code, activating 2FA
  POST /auth/2fa/disable  — Deactivate 2FA (requires a live TOTP code)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES
from src.schemas.two_factor import (
    TotpDisableRequest,
    TotpSetupResponse,
    TotpStatusResponse,
    TotpVerifyRequest,
)
from src.services.totp_service import generate_secret, get_provisioning_uri, verify_totp

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/2fa", tags=["two-factor-auth"], responses=COMMON_RESPONSES)


@router.get("/status", response_model=TotpStatusResponse)
async def get_2fa_status(
    current_user: User = Depends(_get_current_user),
) -> TotpStatusResponse:
    """Return whether 2FA is currently enabled for the authenticated user."""
    return TotpStatusResponse(enabled=current_user.totp_enabled)


@router.post("/setup", response_model=TotpSetupResponse, status_code=status.HTTP_200_OK)
async def setup_2fa(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TotpSetupResponse:
    """Generate a new TOTP secret for the authenticated user.

    This endpoint stores the secret on the user record but does NOT
    activate 2FA yet. The client must call POST /auth/2fa/verify with
    a valid code to confirm the authenticator app is correctly configured.

    Calling this endpoint while 2FA is already active replaces the secret
    (effectively re-enrolment — the old authenticator entry becomes invalid).
    """
    secret = generate_secret()
    account_name = current_user.email

    # Persist the new secret (not yet enabled)
    current_user.totp_secret = secret
    current_user.totp_enabled = False
    await db.flush()
    await db.commit()

    provisioning_uri = get_provisioning_uri(secret, account_name)
    logger.info("2FA setup initiated", extra={"user_id": str(current_user.id)})
    return TotpSetupResponse(provisioning_uri=provisioning_uri, secret=secret)


@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_and_enable_2fa(
    body: TotpVerifyRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Verify a TOTP code and activate 2FA.

    Must be called after POST /auth/2fa/setup. Once the user confirms that
    their authenticator app shows correct codes, 2FA is activated and all
    subsequent logins will require a TOTP code.
    """
    if current_user.totp_secret is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated. Call POST /auth/2fa/setup first.",
        )

    if not verify_totp(current_user.totp_secret, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Check your authenticator app and try again.",
        )

    current_user.totp_enabled = True
    await db.flush()
    await db.commit()

    logger.info("2FA enabled", extra={"user_id": str(current_user.id)})
    return {"message": "Two-factor authentication has been enabled."}


@router.post("/disable", status_code=status.HTTP_200_OK)
async def disable_2fa(
    body: TotpDisableRequest,
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Disable 2FA for the authenticated user.

    Requires a valid TOTP code from the current device to prevent
    an attacker with a stolen session token from removing 2FA protection.
    """
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not currently enabled.",
        )

    if current_user.totp_secret is None or not verify_totp(current_user.totp_secret, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code. Provide a valid code to disable 2FA.",
        )

    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.flush()
    await db.commit()

    logger.info("2FA disabled", extra={"user_id": str(current_user.id)})
    return {"message": "Two-factor authentication has been disabled."}
