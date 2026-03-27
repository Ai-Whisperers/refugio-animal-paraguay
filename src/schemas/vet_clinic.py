"""Pydantic schemas for partner veterinary clinic endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class VetClinicCreate(BaseModel):
    """Request body for POST /api/vet-clinics."""

    name: str = Field(..., min_length=2, max_length=200, description="Clinic name.")
    license_number: str | None = Field(
        None, max_length=100, description="Professional license / registration number."
    )
    email: EmailStr = Field(..., description="Contact email.")
    phone: str = Field(
        ...,
        pattern=r"^\+595\d{6,12}$",
        description="Phone number in Paraguayan format (+595...).",
    )
    contact_person: str = Field(
        ..., min_length=2, max_length=200, description="Primary contact name."
    )
    address: str = Field(..., min_length=5, max_length=500, description="Street address.")
    city: str = Field(..., min_length=2, max_length=100, description="City.")
    department: str | None = Field(
        None, max_length=100, description="Paraguayan department (state)."
    )
    latitude: float | None = Field(
        None, ge=-90, le=90, description="GPS latitude."
    )
    longitude: float | None = Field(
        None, ge=-180, le=180, description="GPS longitude."
    )
    specialties: str | None = Field(
        None, description="Comma-separated specialties (e.g. 'surgery,dentistry')."
    )
    accepts_emergencies: bool = Field(
        False, description="Whether clinic accepts emergency cases."
    )
    notes: str | None = Field(None, description="Internal notes about this clinic.")


class VetClinicUpdate(BaseModel):
    """Request body for PATCH /api/vet-clinics/{id}."""

    name: str | None = Field(None, min_length=2, max_length=200)
    license_number: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, pattern=r"^\+595\d{6,12}$")
    contact_person: str | None = Field(None, min_length=2, max_length=200)
    address: str | None = Field(None, min_length=5, max_length=500)
    city: str | None = Field(None, min_length=2, max_length=100)
    department: str | None = Field(None, max_length=100)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    specialties: str | None = None
    accepts_emergencies: bool | None = None
    notes: str | None = None


class VetClinicStatusUpdate(BaseModel):
    """Request body for PATCH /api/vet-clinics/{id}/status."""

    status: Literal["pending", "active", "suspended", "inactive"] = Field(
        ..., description="New clinic status."
    )


class VetClinicResponse(BaseModel):
    """Response for a single vet clinic."""

    id: UUID
    name: str
    license_number: str | None
    email: str
    phone: str
    contact_person: str
    address: str
    city: str
    department: str | None
    latitude: float | None
    longitude: float | None
    specialties: str | None
    accepts_emergencies: bool
    status: str
    partnership_start: datetime | None
    partnership_end: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VetClinicListResponse(BaseModel):
    """Paginated response for listing vet clinics."""

    items: list[VetClinicResponse]
    total: int
    page: int
    page_size: int
