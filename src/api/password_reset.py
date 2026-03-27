"""Password reset API endpoints.

Endpoints:
  POST /auth/password-reset/request   - Request a password reset email
  POST /auth/password-reset/confirm   - Confirm reset with token + new password
  GET  /auth/password-reset/validate  - Validate a reset token (for frontend)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.db.session import get_db
from src.middleware.rate_limiter import AUTH_RATE_LIMIT, limiter
from src.notifications.service import EmailMessage, EmailService
from src.schemas.password_reset import (
    PasswordResetConfirm,
    PasswordResetConfirmResponse,
    PasswordResetRequest,
    PasswordResetResponse,
)
from src.services.password_reset_service import (
    create_password_reset_token,
    reset_password,
    validate_reset_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/password-reset", tags=["auth"])

PASSWORD_RESET_SUBJECT = "Restablecer contrasena - Refugio Animal Paraguay"


def _build_reset_email_body(reset_url: str) -> str:
    """Build the password reset email body in Spanish."""
    return (
        f"Hola,\n\n"
        f"Recibimos una solicitud para restablecer tu contrasena.\n\n"
        f"Haz clic en el siguiente enlace para crear una nueva contrasena:\n"
        f"{reset_url}\n\n"
        f"Este enlace es valido por 1 hora.\n\n"
        f"Si no solicitaste este cambio, puedes ignorar este mensaje.\n\n"
        f"- Refugio Animal Paraguay"
    )


@router.post("/request", response_model=PasswordResetResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def request_password_reset(
    request: Request,
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PasswordResetResponse:
    """Request a password reset email.

    Always returns success to not reveal whether the email exists.
    """
    token = await create_password_reset_token(db, str(payload.email))

    if token is not None:
        # Build reset URL using the first allowed origin as the frontend base
        frontend_base = settings.allowed_origins_list[0] if settings.allowed_origins_list else "http://localhost:3000"
        reset_url = f"{frontend_base}/admin/reset-password?token={token}"

        try:
            email_service = EmailService(settings)
            message = EmailMessage(
                to=str(payload.email),
                subject=PASSWORD_RESET_SUBJECT,
                html_body=_build_reset_email_body(reset_url),
                text_body=_build_reset_email_body(reset_url),
            )
            await email_service.send_email(message)
        except Exception:
            logger.exception("Failed to send password reset email")

    await db.commit()
    return PasswordResetResponse()


@router.post("/confirm", response_model=PasswordResetConfirmResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def confirm_password_reset(
    request: Request,
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetConfirmResponse:
    """Confirm a password reset using the token and new password."""
    success = await reset_password(db, payload.token, payload.new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please request a new reset link.",
        )

    await db.commit()
    return PasswordResetConfirmResponse(
        message="Password has been reset successfully. You can now log in."
    )


@router.get("/validate")
@limiter.limit(AUTH_RATE_LIMIT)
async def validate_token(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Validate a password reset token (for frontend to check before showing form)."""
    verification_token = await validate_reset_token(db, token)
    return {"valid": verification_token is not None}
