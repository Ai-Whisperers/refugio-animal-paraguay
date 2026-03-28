"""Pydantic schemas for clinic service catalog endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Valid service categories
ServiceCategoryType = Literal[
    "consultation",
    "vaccination",
    "surgery",
    "dental",
    "diagnostic",
    "grooming",
    "emergency",
    "preventive",
    "other",
]


class ClinicServiceCreate(BaseModel):
    """Request body for POST /api/vet-clinics/{clinic_id}/services."""

    name: str = Field(..., min_length=2, max_length=200, description="Service name.")
    description: str | None = Field(
        None, max_length=2000, description="Detailed description of the service."
    )
    category: ServiceCategoryType = Field(default="other", description="Service category.")
    price_pyg: int = Field(..., ge=0, description="Price in Paraguayan Guarani.")
    price_eur: float | None = Field(
        None, ge=0, description="Optional price in EUR for international donors."
    )
    duration_minutes: int | None = Field(None, gt=0, description="Estimated duration in minutes.")
    is_active: bool = Field(default=True, description="Whether this service is active.")


class ClinicServiceUpdate(BaseModel):
    """Request body for PATCH /api/vet-clinics/{clinic_id}/services/{service_id}."""

    name: str | None = Field(None, min_length=2, max_length=200)
    description: str | None = Field(None, max_length=2000)
    category: ServiceCategoryType | None = None
    price_pyg: int | None = Field(None, ge=0)
    price_eur: float | None = Field(None, ge=0)
    duration_minutes: int | None = Field(None, gt=0)
    is_active: bool | None = None


class ClinicServiceResponse(BaseModel):
    """Response for a single clinic service."""

    id: UUID
    clinic_id: UUID
    name: str
    description: str | None
    category: str
    price_pyg: int
    price_eur: float | None
    duration_minutes: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClinicServiceListResponse(BaseModel):
    """Paginated response for listing clinic services."""

    items: list[ClinicServiceResponse]
    total: int
    page: int
    page_size: int
