"""Phone verification API endpoints: send OTP, verify OTP, check status.

Endpoints:
  POST /auth/verify-phone/send-otp   - Send OTP via WhatsApp
  POST /auth/verify-phone/verify-otp - Verify OTP code
  GET  /auth/verify-phone/status      - Check verification status
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import _get_current_user
from src.config import Settings, get_settings
from src.db.models.user import User
from src.db.session import get_db
from src.middleware.rate_limiter import AUTH_RATE_LIMIT, limiter
from src.schemas.error import COMMON_RESPONSES
from src.schemas.phone_verification import (
    PhoneVerificationStatus,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from src.services.phone_verification_service import (
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsError,
    OTPRateLimitError,
    get_verification_status,
    mark_phone_verified,
    send_otp,
    verify_otp,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth/verify-phone",
    tags=["phone-verification"],
    responses=COMMON_RESPONSES,
)

PHONE_PATTERN = r"^\+595\d{9}$"


@router.post("/send-otp", response_model=SendOTPResponse, status_code=status.HTTP_200_OK)
@limiter.limit(AUTH_RATE_LIMIT)
async def send_otp_endpoint(
    request: Request,
    body: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current_user: User = Depends(_get_current_user),
) -> SendOTPResponse:
    """Send a 6-digit OTP via WhatsApp to the user's phone number.

    Requires authentication. The phone number must match +595 format (Paraguay).
    Rate limited to 3 requests per phone per hour.
    """
    try:
        await send_otp(
            db=db,
            phone=body.phone,
            user_id=str(current_user.id),
            settings=settings,
        )
        return SendOTPResponse(
            message="OTP sent via WhatsApp",
            expires_in_seconds=300,
        )
    except OTPRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=exc.message,
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc


@router.post("/verify-otp", response_model=VerifyOTPResponse, status_code=status.HTTP_200_OK)
@limiter.limit(AUTH_RATE_LIMIT)
async def verify_otp_endpoint(
    request: Request,
    body: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> VerifyOTPResponse | JSONResponse:
    """Verify a 6-digit OTP code for a phone number.

    Requires authentication. Max 5 attempts per OTP record.
    After 5 failures, a new OTP must be requested.

    Errors are returned as JSONResponse (not raised) so the DB session
    commits the attempted_count increment rather than rolling back.
    """
    try:
        otp_record = await verify_otp(
            db=db,
            phone=body.phone,
            otp_code=body.otp_code,
        )

        # Mark user phone as verified
        await mark_phone_verified(db, str(current_user.id), body.phone)

        return VerifyOTPResponse(
            message="Phone number verified",
            phone=body.phone,
            verified_at=otp_record.verified_at,
        )
    except OTPExpiredError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "error_code": exc.error_code},
        )
    except OTPInvalidError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "error_code": exc.error_code},
        )
    except OTPMaxAttemptsError as exc:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": exc.message, "error_code": exc.error_code},
        )


@router.get("/status", response_model=PhoneVerificationStatus)
async def phone_verification_status(
    phone: str = Query(..., pattern=PHONE_PATTERN, description="Phone in +595XXXXXXXXX format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user),
) -> PhoneVerificationStatus:
    """Check if a phone number has been verified.

    Requires authentication.
    """
    result = await get_verification_status(db, phone)
    return PhoneVerificationStatus(**result)
