"""Pydantic schemas for public contact and inquiry form submissions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ContactFormCreate(BaseModel):
    """Fields accepted from the general contact form."""

    visitor_name: str = Field(..., min_length=3, max_length=100)
    visitor_email: EmailStr
    subject: str = Field(..., min_length=10, max_length=200)
    message: str = Field(..., min_length=20, max_length=5000)


class AnimalInquiryCreate(BaseModel):
    """Fields accepted from the animal-specific inquiry form."""

    visitor_name: str = Field(..., min_length=3, max_length=100)
    visitor_email: EmailStr
    message: str = Field(..., min_length=20, max_length=5000)


class ContactSubmissionResponse(BaseModel):
    """Confirmation returned after a successful form submission."""

    id: UUID
    form_type: str
    submitted_at: datetime
    message: str = "Your message has been received. We will get back to you soon."
