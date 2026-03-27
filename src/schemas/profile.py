"""Pydantic schemas for user profile management endpoints."""

import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_PARAGUAY_PHONE_PATTERN = re.compile(r"^\+595\d{9}$")
_PASSWORD_STRENGTH_PATTERN = re.compile(
    r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,}$"
)

MAX_FULL_NAME_LENGTH = 100
MAX_PHONE_LENGTH = 20


class ProfileUpdate(BaseModel):
    """Request body for updating user profile information."""
    full_name: str | None = Field(None, max_length=MAX_FULL_NAME_LENGTH)
    phone: str | None = Field(None, max_length=MAX_PHONE_LENGTH)

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: str | None) -> str | None:
        if v is not None and v != "" and not _PARAGUAY_PHONE_PATTERN.match(v):
            msg = "Phone must be in +595XXXXXXXXX format (Paraguay)"
            raise ValueError(msg)
        return v


class ProfileResponse(BaseModel):
    """Response for profile read/update operations."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    full_name: str | None
    email: str
    phone: str | None
    role: str
    is_active: bool
    email_verified: bool


class PasswordChangeRequest(BaseModel):
    """Request body for changing password."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not _PASSWORD_STRENGTH_PATTERN.match(v):
            msg = (
                "Password must be at least 8 characters with 1 uppercase letter, "
                "1 number, and 1 special character"
            )
            raise ValueError(msg)
        return v


class PasswordChangeResponse(BaseModel):
    """Response for password change operation."""
    message: str


class SimplePreferencesUpdate(BaseModel):
    """Simplified notification preferences for the portal profile page."""
    email_adoption: bool = True
    email_donations: bool = True
    email_volunteer: bool = True
    whatsapp_enabled: bool = False
    inapp_enabled: bool = True


class SimplePreferencesResponse(BaseModel):
    """Response for simplified notification preferences."""
    email_adoption: bool
    email_donations: bool
    email_volunteer: bool
    whatsapp_enabled: bool
    inapp_enabled: bool


class AccountDeleteRequest(BaseModel):
    """Request body for initiating account deletion."""
    password: str = Field(..., min_length=1, description="Current password for verification")


class AccountDeleteResponse(BaseModel):
    """Response for account deletion request."""
    message: str
    confirmation_required: bool = True


class AccountDeleteConfirm(BaseModel):
    """Request body for confirming account deletion via token."""
    token: str = Field(..., min_length=1)


class AccountDeleteConfirmResponse(BaseModel):
    """Response for confirmed account deletion."""
    message: str
    deleted: bool
