"""Auth router: login, user creation, password reset, current user.

Endpoints:
  POST /auth/token                    — email + password -> JWT access token
  POST /auth/users                    — admin only: create staff/admin user
  GET  /auth/me                       — current authenticated user info
  POST /auth/password-reset-request   — request password reset (public)
  POST /auth/password-reset/{token}   — complete password reset (public)
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.auth.password_reset import (
    PasswordUnchangedError,
    create_password_reset_token,
    validate_and_reset_password,
)
from src.auth.utils import create_access_token, hash_password, verify_password
from src.config import Settings, get_settings
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.password_reset import (
    PasswordResetComplete,
    PasswordResetCompleteResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)
from src.schemas.user import TokenResponse, UserCreate, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate with email + password and return a JWT access token."""
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()

    if (
        user is None
        or not user.is_active
        or not verify_password(form.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={"sub": str(user.id)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return TokenResponse(access_token=token)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> User:
    """Create a new staff or admin user. Admin access required."""
    existing = await db.execute(select(User).where(User.email == str(payload.email)))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=str(payload.email),
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(require_staff)) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post(
    "/password-reset-request",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetResponse:
    """Request a password reset link. Always returns 200 to prevent enumeration."""
    token = await create_password_reset_token(db, str(payload.email))
    await db.commit()

    if token is not None:
        # V1: log the token instead of sending email (no SMTP configured yet).
        # In production, this would dispatch an async email via BackgroundTasks.
        logger.info(
            "Password reset token generated (email delivery stubbed for V1). " "Token: %s",
            token,
        )

    return PasswordResetResponse()


@router.post(
    "/password-reset/{token}",
    response_model=PasswordResetCompleteResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_password_reset(
    token: str,
    payload: PasswordResetComplete,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetCompleteResponse:
    """Complete a password reset using a valid token and new password."""
    try:
        success = await validate_and_reset_password(db, token, payload.new_password)
    except PasswordUnchangedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        ) from exc

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired reset token",
        )

    await db.commit()
    return PasswordResetCompleteResponse()
