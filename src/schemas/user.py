"""Pydantic schemas for user auth endpoints."""

import re
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.db.models.user import UserRole


class PublicRegistrationRole(StrEnum):
    """Roles available for public self-registration."""

    ADOPTER = "adopter"
    DONOR = "donor"
    VOLUNTEER = "volunteer"
    FOSTER = "foster"


class UserCreate(BaseModel):
    """Admin-only user creation (staff/admin/vet)."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.STAFF


# Paraguay phone number pattern: +595 followed by 9 digits
PARAGUAY_PHONE_PATTERN = re.compile(r"^\+595\d{9}$")

# Password must have: 1 uppercase, 1 digit, 1 special character, min 8 chars
PASSWORD_UPPERCASE_PATTERN = re.compile(r"[A-Z]")
PASSWORD_DIGIT_PATTERN = re.compile(r"\d")
PASSWORD_SPECIAL_PATTERN = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")
MIN_PASSWORD_LENGTH = 8


class PublicUserRegister(BaseModel):
    """Public self-registration request payload."""

    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., max_length=20)
    password: str = Field(..., min_length=MIN_PASSWORD_LENGTH)
    role: PublicRegistrationRole

    @field_validator("full_name")
    @classmethod
    def strip_and_validate_name(cls, v: str) -> str:
        """Strip whitespace and validate name length."""
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Full name must be at least 2 characters after trimming whitespace")
        return stripped

    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """Validate Paraguay phone format: +595XXXXXXXXX (9 digits after country code)."""
        cleaned = v.strip()
        if not PARAGUAY_PHONE_PATTERN.match(cleaned):
            raise ValueError(
                "Phone must be in Paraguay format: +595 followed by 9 digits (e.g., +595981234567)"
            )
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce password strength: 1 uppercase, 1 digit, 1 special character."""
        errors: list[str] = []
        if not PASSWORD_UPPERCASE_PATTERN.search(v):
            errors.append("at least 1 uppercase letter")
        if not PASSWORD_DIGIT_PATTERN.search(v):
            errors.append("at least 1 number")
        if not PASSWORD_SPECIAL_PATTERN.search(v):
            errors.append("at least 1 special character")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v


class PublicUserRegisterResponse(BaseModel):
    """Response after successful public registration."""

    user_id: UUID
    message: str = "Registration successful. Check your email for verification link."
    next_step: str = "verify_email"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None = None
    phone: str | None = None
    role: UserRole
    is_active: bool
    email_verified: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
