"""Pydantic schemas for password reset and email verification endpoints."""

from pydantic import BaseModel, EmailStr, Field


class EmailRequest(BaseModel):
    """Request body for endpoints that accept only an email address.

    Used by: resend-verification, password-reset initiation.
    """

    email: EmailStr


class VerifyEmailRequest(BaseModel):
    """Request body for the email verification endpoint."""

    token: str = Field(..., min_length=1)


class PasswordResetConfirmRequest(BaseModel):
    """Request body for completing a password reset."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Generic message response for endpoints that return status text."""

    message: str
