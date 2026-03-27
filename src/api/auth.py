"""Auth router: login, user creation (admin only), current user.

Endpoints:
  POST /auth/token   — email + password → JWT access token
  POST /auth/users   — admin only: create staff/admin user
  GET  /auth/me      — current authenticated user info
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.email_verification import _send_verification_email
from src.auth.dependencies import require_admin, require_staff
from src.auth.utils import create_access_token, hash_password, verify_password
from src.config import Settings, get_settings
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import AUTH_RATE_LIMIT, limiter
from src.schemas.user import TokenResponse, UserCreate, UserResponse
from src.services.email_verification_service import create_email_verification_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
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

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox for the verification link.",
        )

    token = create_access_token(
        data={"sub": str(user.id)},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return TokenResponse(access_token=token)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def create_user(
    request: Request,
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> User:
    """Create a new staff or admin user. Admin access required.

    Sends a verification email to the new user. The user must verify
    their email before they can log in.
    """
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
        email_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Send verification email (best-effort — don't fail user creation)
    try:
        token = await create_email_verification_token(db, str(user.id))
        if token:
            await _send_verification_email(str(user.email), token, settings)
    except Exception:
        logger.warning(
            "Failed to send verification email for user_id=%s", user.id
        )

    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(require_staff)) -> User:
    """Return the currently authenticated user."""
    return current_user
