"""Profile management router for user self-service operations."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.schemas.profile import (
    AccountDeleteConfirm,
    AccountDeleteConfirmResponse,
    AccountDeleteRequest,
    AccountDeleteResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    ProfileResponse,
    ProfileUpdate,
    SimplePreferencesResponse,
    SimplePreferencesUpdate,
)
from src.services.profile_service import (
    change_password,
    confirm_account_deletion,
    export_user_data,
    get_simple_preferences,
    request_account_deletion,
    update_profile,
    update_simple_preferences,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portal", tags=["portal-profile"], responses=AUTHENTICATED_RESPONSES)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: User = Depends(_get_current_user)) -> ProfileResponse:
    """Return the current user's profile information."""
    return ProfileResponse.model_validate(user)


@router.put("/profile", response_model=ProfileResponse)
async def update_user_profile(
    payload: ProfileUpdate, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Update the current user's personal information."""
    updated = await update_profile(db, user, full_name=payload.full_name, phone=payload.phone)
    return ProfileResponse.model_validate(updated)


@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_user_password(
    payload: PasswordChangeRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db),
) -> PasswordChangeResponse:
    """Change the current user's password."""
    success = await change_password(db, user, payload.current_password, payload.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect or new password matches current password",
        )
    return PasswordChangeResponse(message="Password changed successfully")


@router.get("/preferences", response_model=SimplePreferencesResponse)
async def get_preferences(
    user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db),
) -> SimplePreferencesResponse:
    """Get the current user's notification preferences."""
    prefs = await get_simple_preferences(db, user.id)
    return SimplePreferencesResponse(**prefs)


@router.put("/preferences", response_model=SimplePreferencesResponse)
async def update_preferences(
    payload: SimplePreferencesUpdate, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db),
) -> SimplePreferencesResponse:
    """Update the current user's notification preferences."""
    updated = await update_simple_preferences(db, user.id, payload.model_dump())
    return SimplePreferencesResponse(**updated)


@router.get("/gdpr/export")
async def gdpr_export(
    user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Download all personal data as JSON (GDPR Article 15 & 20)."""
    data = await export_user_data(db, user)
    export_date = data["export_date"][:10]
    filename = f"refugio_data_{export_date}.json"
    return JSONResponse(content=data, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.post("/gdpr/delete", response_model=AccountDeleteResponse)
async def gdpr_delete_request(
    payload: AccountDeleteRequest, user: User = Depends(_get_current_user), db: AsyncSession = Depends(get_db),
) -> AccountDeleteResponse:
    """Request account deletion. Requires password re-entry."""
    token = await request_account_deletion(db, user, payload.password)
    if token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")
    logger.info("Account deletion token created for user %s", str(user.id)[:8] + "...")
    return AccountDeleteResponse(
        message="A confirmation email has been sent. Please click the link to confirm account deletion.",
        confirmation_required=True,
    )


@router.post("/gdpr/delete/confirm", response_model=AccountDeleteConfirmResponse)
async def gdpr_delete_confirm(
    payload: AccountDeleteConfirm, db: AsyncSession = Depends(get_db),
) -> AccountDeleteConfirmResponse:
    """Confirm account deletion using the emailed token."""
    success = await confirm_account_deletion(db, payload.token)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired deletion token")
    return AccountDeleteConfirmResponse(message="Your account has been deleted and personal data anonymized.", deleted=True)
