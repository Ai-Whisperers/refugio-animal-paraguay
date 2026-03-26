"""Pydantic schemas for In-Kind Donation resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.donation import CurrencyCode, ItemType


class InKindDonationCreate(BaseModel):
    """Fields for recording an in-kind donation."""

    donor_id: UUID | None = None
    item_type: ItemType
    description: str | None = Field(default=None, max_length=500)
    quantity: int = Field(default=1, gt=0)
    estimated_value_cents: int = Field(..., ge=0)
    currency: CurrencyCode = CurrencyCode.EUR
    date_received: datetime | None = None
    notes: str | None = None


class InKindDonationUpdate(BaseModel):
    """Fields for updating an in-kind donation. All optional."""

    item_type: ItemType | None = None
    description: str | None = Field(default=None, max_length=500)
    quantity: int | None = Field(default=None, gt=0)
    estimated_value_cents: int | None = Field(default=None, ge=0)
    currency: CurrencyCode | None = None
    date_received: datetime | None = None
    notes: str | None = None


class InKindDonationResponse(BaseModel):
    """Shape returned for an in-kind donation record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donor_id: UUID | None
    item_type: ItemType
    description: str | None
    quantity: int
    estimated_value_cents: int
    currency: CurrencyCode
    date_received: datetime
    received_by_staff_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class InKindDonationListResponse(BaseModel):
    """Paginated list of in-kind donations."""

    items: list[InKindDonationResponse]
    total: int
    limit: int
    offset: int


class DonorGivingSummary(BaseModel):
    """Combined cash + in-kind giving summary for a donor."""

    donor_id: UUID
    donor_name: str
    cash_total_cents: int
    cash_donation_count: int
    in_kind_total_cents: int
    in_kind_donation_count: int
    combined_total_cents: int
    currency: str
