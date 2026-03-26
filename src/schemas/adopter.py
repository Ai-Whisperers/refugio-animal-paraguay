"""Pydantic schemas for the Adopter resource."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdopterCreate(BaseModel):
    """Fields accepted when registering a new adopter."""

    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    # Consent can be granted at registration time (common for online forms)
    gdpr_consent_at: datetime | None = None


class AdopterUpdate(BaseModel):
    """All fields optional — only provided fields are written on PATCH."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    # Setting to a timestamp grants consent; API does not allow revoking via PATCH
    gdpr_consent_at: datetime | None = None


class AdopterResponse(BaseModel):
    """Shape returned by every Adopter endpoint."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    phone: str | None
    address: str | None
    gdpr_consent_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # deleted_at intentionally omitted from response — soft-deleted records are not returned
