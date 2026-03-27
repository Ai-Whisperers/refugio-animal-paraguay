"""Pydantic schemas for external veterinary referrals."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.vet_referral import ReferralStatus, ReferralUrgency


class VetReferralCreate(BaseModel):
    """Schema for creating a new vet referral."""

    animal_id: UUID
    external_vet_name: str = Field(..., min_length=1, max_length=255)
    external_vet_clinic: str | None = Field(None, max_length=255)
    external_vet_phone: str | None = Field(None, max_length=50)
    external_vet_email: str | None = Field(None, max_length=255)
    reason: str = Field(..., min_length=1)
    specialty: str | None = Field(None, max_length=100)
    urgency: ReferralUrgency = ReferralUrgency.MEDIUM
    appointment_date: datetime | None = None
    estimated_cost: float | None = Field(None, ge=0, le=999999.99)


class VetReferralUpdate(BaseModel):
    """Schema for updating a vet referral."""

    external_vet_name: str | None = Field(None, min_length=1, max_length=255)
    external_vet_clinic: str | None = None
    external_vet_phone: str | None = None
    external_vet_email: str | None = None
    reason: str | None = Field(None, min_length=1)
    specialty: str | None = None
    urgency: ReferralUrgency | None = None
    status: ReferralStatus | None = None
    appointment_date: datetime | None = None
    diagnosis: str | None = None
    treatment_notes: str | None = None
    follow_up_required: bool | None = None
    follow_up_date: datetime | None = None
    estimated_cost: float | None = Field(None, ge=0, le=999999.99)
    actual_cost: float | None = Field(None, ge=0, le=999999.99)


class VetReferralResponse(BaseModel):
    """Schema for returning a vet referral."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    animal_id: UUID
    referred_by_id: UUID | None = None
    external_vet_name: str
    external_vet_clinic: str | None = None
    external_vet_phone: str | None = None
    external_vet_email: str | None = None
    reason: str
    specialty: str | None = None
    urgency: str
    status: str
    appointment_date: datetime | None = None
    diagnosis: str | None = None
    treatment_notes: str | None = None
    follow_up_required: bool
    follow_up_date: datetime | None = None
    estimated_cost: float | None = None
    actual_cost: float | None = None
    created_at: datetime
    updated_at: datetime


class VetReferralListResponse(BaseModel):
    """Paginated list response for vet referrals."""

    items: list[VetReferralResponse]
    total: int
    offset: int
    limit: int
