"""Email verification API endpoints.

Endpoints:
  POST /auth/email/verify         - Verify email with token
  POST /auth/email/resend         - Resend verification email
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import AUTH_RATE_LIMIT, limiter
from src.notifications.service import EmailMessage, EmailService
from src.notifications.templates import TemplateRenderer
from src.schemas.error import COMMON_RESPONSES
from src.services.email_verification_service import (
    create_email_verification_token,
    verify_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/email", tags=["auth"], responses=COMMON_RESPONSES)

FRONTEND_BASE_URL = "http://localhost:3000"

_template_renderer = TemplateRenderer()


class EmailVerifyRequest(BaseModel):
    """Request body for email verification."""

    token: str


class EmailResendRequest(BaseModel):
    """Request body to resend verification email."""

    email: EmailStr


class EmailVerifyResponse(BaseModel):
    """Response for email verification."""

    verified: bool
    message: str


def _build_verification_url(token: str) -> str:
    """Build the frontend verification URL."""
    return f"{FRONTEND_BASE_URL}/admin/verify-email?token={token}"


async def _send_verification_email(email: str, token: str, settings: Settings) -> None:
    """Send a verification email with the token link."""
    verification_url = _build_verification_url(token)

    html_body = _template_renderer.render(
        "email_verification",
        {"user_email": email, "verification_url": verification_url},
    )

    email_service = EmailService(settings)
    message = EmailMessage(
        to=email,
        subject="Verifica tu email - Refugio Animal Paraguay",
        html_body=html_body,
    )
    await email_service.send_email(message)


@router.post("/verify", response_model=EmailVerifyResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def verify_email_endpoint(
    request: Request,
    payload: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailVerifyResponse:
    """Verify an email address using a verification token."""
    success = await verify_email(db, payload.token)
    await db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido o expirado. Solicita un nuevo enlace de verificacion.",
        )

    return EmailVerifyResponse(
        verified=True,
        message="Email verificado exitosamente. Ya puedes iniciar sesion.",
    )


@router.post("/resend", response_model=EmailVerifyResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def resend_verification_email(
    request: Request,
    payload: EmailResendRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EmailVerifyResponse:
    """Resend email verification link.

    Always returns success to not leak whether the email exists.
    """
    result = await db.execute(select(User).where(User.email == str(payload.email)))
    user = result.scalar_one_or_none()

    if user is not None and user.is_active and not user.email_verified:
        token = await create_email_verification_token(db, str(user.id))
        if token:
            await _send_verification_email(str(user.email), token, settings)
        await db.commit()

    return EmailVerifyResponse(
        verified=False,
        message="Si este email esta registrado y no verificado, recibiras un nuevo enlace.",
    )
