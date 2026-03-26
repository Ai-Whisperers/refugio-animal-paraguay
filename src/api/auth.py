"""Auth router: login, user creation, email verification, password reset.

Endpoints:
  POST /auth/token                  -- email + password -> JWT access token
  POST /auth/users                  -- admin only: create staff/admin user
  GET  /auth/me                     -- current authenticated user info
  POST /auth/verify-email           -- verify email with token
  POST /auth/resend-verification    -- resend verification email
  POST /auth/password-reset         -- initiate password reset
  POST /auth/password-reset/confirm -- complete password reset with token
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.auth.email_backend import send_password_reset_email, send_verification_email
from src.auth.token_service import create_verification_token, validate_and_consume_token
from src.auth.utils import create_access_token, hash_password, verify_password
from src.config import Settings, get_settings
from src.db.models.user import User
from src.db.models.verification_token import TokenType
from src.db.session import get_db
from src.schemas.password_reset import (
    EmailRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    VerifyEmailRequest,
)
from src.schemas.user import TokenResponse, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Uniform message to prevent account enumeration
_GENERIC_EMAIL_MSG = (
    "If an account exists with that email, the requested action has been initiated. "
    "Please check your inbox."
)


@router.post("/token", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate with email + password and return a JWT access token."""
    result = await db.execute(select(User).where(User.email == func.lower(form.username)))
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

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox or request a new verification email.",
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
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> User:
    """Create a new staff or admin user. Admin access required.

    Sends a verification email to the new user.
    """
    email_lower = str(payload.email).lower()
    existing = await db.execute(select(User).where(User.email == email_lower))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=email_lower,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Generate verification token and queue email
    token = await create_verification_token(db, user.id, TokenType.EMAIL_VERIFY)
    background_tasks.add_task(send_verification_email, user.email, token)

    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(require_staff)) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Verify a user's email address using the token from the verification email."""
    user_id = await validate_and_consume_token(db, payload.token, TokenType.EMAIL_VERIFY)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )

    user.is_verified = True
    user.updated_at = datetime.now(UTC)
    await db.flush()

    return MessageResponse(message="Email verified successfully.")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    payload: EmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Resend the verification email.

    Returns a generic success message regardless of whether the email exists,
    to prevent account enumeration.
    """
    email_lower = str(payload.email).lower()
    result = await db.execute(select(User).where(User.email == email_lower))
    user = result.scalar_one_or_none()

    if user is not None and not user.is_verified:
        token = await create_verification_token(db, user.id, TokenType.EMAIL_VERIFY)
        background_tasks.add_task(send_verification_email, user.email, token)

    return MessageResponse(message=_GENERIC_EMAIL_MSG)


@router.post("/password-reset", response_model=MessageResponse)
async def initiate_password_reset(
    payload: EmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Initiate a password reset by sending a reset token to the user's email.

    Returns a generic success message regardless of whether the email exists,
    to prevent account enumeration.
    """
    email_lower = str(payload.email).lower()
    result = await db.execute(select(User).where(User.email == email_lower))
    user = result.scalar_one_or_none()

    if user is not None and user.is_active:
        token = await create_verification_token(db, user.id, TokenType.PASSWORD_RESET)
        background_tasks.add_task(send_password_reset_email, user.email, token)

    return MessageResponse(message=_GENERIC_EMAIL_MSG)


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Complete a password reset using the token and a new password."""
    user_id = await validate_and_consume_token(db, payload.token, TokenType.PASSWORD_RESET)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    user.hashed_password = hash_password(payload.new_password)
    user.updated_at = datetime.now(UTC)
    await db.flush()

    return MessageResponse(
        message="Password reset successfully. You can now log in with your new password."
    )
