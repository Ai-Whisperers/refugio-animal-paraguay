"""Pydantic schemas for password reset endpoints."""

from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    """Request body for POST /auth/password-reset-request."""

    email: EmailStr


class PasswordResetComplete(BaseModel):
    """Request body for POST /auth/password-reset/{token}."""

    new_password: str = Field(
        ...,
        min_length=8,
        description="New password, minimum 8 characters.",
    )


class PasswordResetResponse(BaseModel):
    """Generic success response — identical for all outcomes to prevent info leaks."""

    message: str = Field(
        default="If an account with that email exists, a password reset link has been sent."
    )


class PasswordResetCompleteResponse(BaseModel):
    """Response after successful password reset."""

    message: str = Field(default="Password has been reset successfully.")
