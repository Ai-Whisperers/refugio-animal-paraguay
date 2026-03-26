"""Pydantic schemas for public adoption application submissions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class PublicAdoptionApplicationCreate(BaseModel):
    """Fields accepted from a public adoption application form."""

    animal_id: UUID
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    message: str | None = Field(default=None, max_length=2000)
    gdpr_consent: bool = Field(
        ...,
        description="Applicant must explicitly consent to data processing",
    )


class PublicAdoptionApplicationResponse(BaseModel):
    """Confirmation returned after a successful adoption application."""

    id: UUID
    animal_id: UUID
    status: str
    submitted_at: datetime
    message: str = "Your adoption application has been submitted successfully."
