"""Pydantic schemas for in-kind (non-cash) donation resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.donation import CurrencyCode
from src.db.models.in_kind_donation import ItemType


class InKindDonationCreate(BaseModel):
    """Fields for recording an in-kind donation."""

    donor_id: UUID | None = None
    item_type: ItemType
    description: str = Field(..., min_length=1, max_length=500)
    quantity: int = Field(default=1, ge=1)
    # Estimated value in smallest currency unit (cents/guaranies)
    estimated_value_cents: int = Field(..., gt=0)
    currency: CurrencyCode = CurrencyCode.PYG
    date_received: datetime | None = None
    notes: str | None = None


class InKindDonationResponse(BaseModel):
    """Shape returned for an in-kind donation record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donor_id: UUID | None
    item_type: ItemType
    description: str
    quantity: int
    estimated_value_cents: int
    currency: CurrencyCode
    date_received: datetime
    received_by_user_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class InKindDonationListResponse(BaseModel):
    """Paginated response for in-kind donations."""

    items: list[InKindDonationResponse]
    total: int
    page: int
    page_size: int
