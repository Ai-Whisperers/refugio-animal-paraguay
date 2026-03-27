"""Email verification API endpoints.

Endpoints:
  GET  /auth/verify-email?token=X  - Verify email via link click (browser-friendly)
  POST /auth/email/verify          - Verify email with token (API-friendly)
  POST /auth/email/resend          - Resend verification email
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import limiter
from src.notifications.service import EmailMessage, EmailService
from src.notifications.templates import TemplateRenderer
from src.schemas.error import COMMON_RESPONSES
from src.services.email_verification_service import (
    VerificationResult,
    create_email_verification_token,
    verify_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"], responses=COMMON_RESPONSES)

FRONTEND_BASE_URL = "http://localhost:3000"

# Rate limit for resend: 3 per hour per endpoint (per-email limiting via app logic)
RESEND_RATE_LIMIT = "3/hour"

_template_renderer = TemplateRenderer()

# Error messages mapped to verification result codes
_VERIFICATION_ERROR_MESSAGES = {
    VerificationResult.TOKEN_NOT_FOUND: (
        "Token invalido. Verifica que el enlace sea correcto.",
        "invalid_token",
    ),
    VerificationResult.TOKEN_EXPIRED: (
        "Token expirado. Los enlaces de verificacion son validos por 24 horas. "
        "Solicita un nuevo enlace.",
        "token_expired",
    ),
    VerificationResult.TOKEN_ALREADY_USED: (
        "Este enlace de verificacion ya fue utilizado. "
        "Si necesitas un nuevo enlace, solicita uno nuevo.",
        "token_already_used",
    ),
    VerificationResult.USER_NOT_FOUND: (
        "No se encontro la cuenta asociada a este enlace.",
        "user_not_found",
    ),
}


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
    error_code: str | None = None


def _build_verification_url(token: str) -> str:
    """Build the frontend verification URL."""
    return f"{FRONTEND_BASE_URL}/auth/verify-email?token={token}"


def _build_resend_url(email: str) -> str:
    """Build the resend verification email URL."""
    return f"{FRONTEND_BASE_URL}/auth/resend-verification?email={email}"


async def _send_verification_email(
    email: str,
    token: str,
    settings: Settings,
    user_name: str | None = None,
) -> None:
    """Send a verification email with the token link."""
    verification_url = _build_verification_url(token)

    template_data = {
        "user_email": email,
        "user_name": user_name or email.split("@")[0],
        "verification_url": verification_url,
        "resend_url": _build_resend_url(email),
        "expiry_hours": 24,
    }

    html_body = _template_renderer.render(
        "email_verification",
        template_data,
    )

    email_service = EmailService(settings)
    message = EmailMessage(
        to=email,
        subject="Verifica tu email - Refugio Animal Paraguay",
        html_body=html_body,
    )
    await email_service.send_email(message)


def _handle_verification_error(result: VerificationResult) -> None:
    """Raise HTTPException with specific error code for failed verification."""
    message, error_code = _VERIFICATION_ERROR_MESSAGES[result]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"message": message, "error_code": error_code},
    )


@router.get("/verify-email", response_model=EmailVerifyResponse)
async def verify_email_get(
    request: Request,
    token: str = Query(..., description="Verification token from email link"),
    db: AsyncSession = Depends(get_db),
) -> EmailVerifyResponse:
    """Verify an email address via GET (browser-friendly for email link clicks).

    This endpoint is designed to be called when a user clicks the
    verification link in their email.
    """
    result = await verify_email(db, token)
    await db.commit()

    if result != VerificationResult.SUCCESS:
        _handle_verification_error(result)

    return EmailVerifyResponse(
        verified=True,
        message="Email verificado exitosamente. Ya puedes iniciar sesion.",
    )


@router.post("/email/verify", response_model=EmailVerifyResponse)
async def verify_email_endpoint(
    request: Request,
    payload: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailVerifyResponse:
    """Verify an email address using a verification token (API-friendly)."""
    result = await verify_email(db, payload.token)
    await db.commit()

    if result != VerificationResult.SUCCESS:
        _handle_verification_error(result)

    return EmailVerifyResponse(
        verified=True,
        message="Email verificado exitosamente. Ya puedes iniciar sesion.",
    )


@router.post("/email/resend", response_model=EmailVerifyResponse)
@limiter.limit(RESEND_RATE_LIMIT)
async def resend_verification_email(
    request: Request,
    payload: EmailResendRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EmailVerifyResponse:
    """Resend email verification link.

    Rate limited to 3 requests per hour. Always returns success
    to not leak whether the email exists.
    """
    result = await db.execute(select(User).where(User.email == str(payload.email)))
    user = result.scalar_one_or_none()

    if user is not None and user.is_active and not user.email_verified:
        token = await create_email_verification_token(db, str(user.id))
        if token:
            user_name = getattr(user, "full_name", None)
            await _send_verification_email(str(user.email), token, settings, user_name=user_name)
        await db.commit()

    return EmailVerifyResponse(
        verified=False,
        message="Si este email esta registrado y no verificado, recibiras un nuevo enlace.",
    )
