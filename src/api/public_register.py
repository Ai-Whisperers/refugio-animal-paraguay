"""Public user registration API endpoint.

Endpoints:
  POST /auth/register  - Self-registration for public users (adopter/donor/volunteer/foster)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.email_verification import _send_verification_email
from src.auth.utils import hash_password
from src.config import Settings, get_settings
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import AUTH_RATE_LIMIT, limiter
from src.schemas.error import COMMON_RESPONSES
from src.schemas.user import PublicUserRegister, PublicUserRegisterResponse
from src.services.email_verification_service import create_email_verification_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"], responses=COMMON_RESPONSES)


@router.post(
    "/register",
    response_model=PublicUserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(AUTH_RATE_LIMIT)
async def register_public_user(
    request: Request,
    payload: PublicUserRegister,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PublicUserRegisterResponse:
    """Register a new public user (adopter, donor, volunteer, or foster).

    Creates an unverified user account and sends a verification email.
    The user must verify their email before logging in.
    """
    # Check for duplicate email or phone
    result = await db.execute(
        select(User).where(
            or_(
                User.email == str(payload.email),
                User.phone == payload.phone,
            )
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        if existing_user.email == str(payload.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this phone number already exists",
        )

    # Create user with unverified status
    user = User(
        full_name=payload.full_name,
        email=str(payload.email),
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=payload.role.value,
        email_verified=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Send verification email (best-effort)
    try:
        token = await create_email_verification_token(db, str(user.id))
        if token:
            await _send_verification_email(str(user.email), token, settings)
    except Exception:
        logger.warning(
            "Failed to send verification email for new registration, user_id=%s",
            user.id,
        )

    await db.commit()

    logger.info(
        "New public user registered: user_id=%s, role=%s",
        user.id,
        user.role,
    )

    return PublicUserRegisterResponse(user_id=user.id)
