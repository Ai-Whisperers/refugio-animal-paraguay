"""Two-Factor Authentication router.

Endpoints:
  GET    /auth/2fa/status                   — Return whether 2FA is enabled for the current user
  POST   /auth/2fa/setup                    — Generate a new TOTP secret (does NOT activate 2FA yet)
  POST   /auth/2fa/verify                   — Confirm the first TOTP code, activating 2FA
  POST   /auth/2fa/disable                  — Deactivate 2FA (requires a live TOTP code)
  POST   /auth/2fa/backup-codes             — Generate a fresh batch of backup recovery codes
  GET    /auth/2fa/backup-codes/count       — Return the number of unused backup codes remaining
  DELETE /auth/2fa/admin/users/{user_id}    — Admin: reset 2FA for a locked-out user
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user, require_admin
from src.db.models.totp_backup_code import TotpBackupCode
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES, COMMON_RESPONSES
from src.schemas.two_factor import (
    BackupCodesCountResponse,
    BackupCodesResponse,
    TotpDisableRequest,
    TotpSetupResponse,
    TotpStatusResponse,
    TotpVerifyRequest,
)
from src.services.backup_code_service import (
    count_remaining_backup_codes,
    generate_backup_codes,
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


@router.post(
    "/backup-codes",
    response_model=BackupCodesResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_new_backup_codes(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BackupCodesResponse:
    """Generate a fresh batch of backup recovery codes.

    Requires 2FA to be enabled. Calling this endpoint invalidates all
    previously issued codes (used or not) and returns a new set of plain-text
    codes. Present these to the user exactly once — they are stored hashed and
    cannot be retrieved again.
    """
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA must be enabled before generating backup codes.",
        )

    plain_codes = await generate_backup_codes(db, current_user.id)
    await db.commit()

    logger.info(
        "Backup codes regenerated",
        extra={"user_id": str(current_user.id), "count": len(plain_codes)},
    )
    return BackupCodesResponse(codes=plain_codes)


@router.get(
    "/backup-codes/count",
    response_model=BackupCodesCountResponse,
    status_code=status.HTTP_200_OK,
)
async def get_backup_codes_count(
    current_user: User = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BackupCodesCountResponse:
    """Return the number of unused backup codes remaining for the authenticated user."""
    remaining = await count_remaining_backup_codes(db, current_user.id)
    return BackupCodesCountResponse(remaining=remaining)


# ---------------------------------------------------------------------------
# Admin recovery — reset 2FA for a locked-out user
# ---------------------------------------------------------------------------

_ADMIN_2FA_RESPONSES = {
    **AUTHENTICATED_RESPONSES,
    404: {"description": "User not found"},
}


@router.delete(
    "/admin/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_ADMIN_2FA_RESPONSES,
)
async def admin_reset_2fa(
    user_id: UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Disable 2FA and revoke all backup codes for the specified user.

    Reserved for administrators to unblock staff members who have lost access
    to both their authenticator device and their backup codes.  The user will
    be able to re-enrol in 2FA after logging in again.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )

    # Revoke all backup codes first
    await db.execute(delete(TotpBackupCode).where(TotpBackupCode.user_id == user_id))

    # Clear 2FA fields
    target_user.totp_enabled = False
    target_user.totp_secret = None

    await db.flush()
    await db.commit()

    logger.info(
        "Admin reset 2FA for user",
        extra={"admin_id": str(_admin.id), "target_user_id": str(user_id)},
    )
