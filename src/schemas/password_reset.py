"""Pydantic schemas for password reset endpoints."""

from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    """Request body for initiating a password reset."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Request body for confirming a password reset with token + new password."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class PasswordResetResponse(BaseModel):
    """Response for password reset request (always succeeds to not leak email existence)."""

    message: str = "If this email is registered, a reset link has been sent."


class PasswordResetConfirmResponse(BaseModel):
    """Response for password reset confirmation."""

    message: str
