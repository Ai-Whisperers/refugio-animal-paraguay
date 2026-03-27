"""Pydantic schemas for phone verification OTP endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class SendOTPRequest(BaseModel):
    """Request body for POST /auth/verify-phone/send-otp."""

    phone: str = Field(
        ...,
        pattern=r"^\+595\d{9}$",
        description="Phone number in +595XXXXXXXXX format (Paraguay).",
        examples=["+595981234567"],
    )


class SendOTPResponse(BaseModel):
    """Response for a successful OTP send request."""

    message: str = "OTP sent via WhatsApp"
    expires_in_seconds: int = 300


class VerifyOTPRequest(BaseModel):
    """Request body for POST /auth/verify-phone/verify-otp."""

    phone: str = Field(
        ...,
        pattern=r"^\+595\d{9}$",
        description="Phone number in +595XXXXXXXXX format (Paraguay).",
    )
    otp_code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit OTP code.",
    )


class VerifyOTPResponse(BaseModel):
    """Response for a successful OTP verification."""

    message: str = "Phone number verified"
    phone: str
    verified_at: datetime


class PhoneVerificationStatus(BaseModel):
    """Response for GET /auth/verify-phone/status."""

    verified: bool
    verified_at: datetime | None = None


class PhoneVerificationError(BaseModel):
    """Error response with structured error code."""

    detail: str
    error_code: str | None = None
