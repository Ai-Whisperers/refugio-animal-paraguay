"""Pydantic schemas for veterinary voucher endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

VoucherStatusType = Literal["purchased", "assigned", "redeemed", "expired", "cancelled"]


class VetVoucherCreate(BaseModel):
    """Request body for POST /api/vet-vouchers."""

    amount_pyg: int = Field(..., gt=0, description="Voucher value in PYG.")
    amount_eur: float | None = Field(None, gt=0, description="Original EUR amount paid by donor.")
    donor_id: UUID | None = Field(None, description="Donor who purchased the voucher.")
    clinic_id: UUID | None = Field(None, description="Restrict to a specific clinic (NULL = any).")
    service_category: str | None = Field(
        None, max_length=50, description="Restrict to a service category."
    )
    expires_at: datetime = Field(..., description="Voucher expiry date.")
    notes: str | None = Field(None, max_length=2000, description="Optional notes.")


class VetVoucherAssign(BaseModel):
    """Request body for POST /api/vet-vouchers/{id}/assign."""

    beneficiary_id: UUID = Field(..., description="User to assign the voucher to.")


class VetVoucherRedeem(BaseModel):
    """Request body for POST /api/vet-vouchers/{id}/redeem."""

    clinic_id: UUID = Field(..., description="Clinic where the voucher is being redeemed.")
    service_id: UUID | None = Field(None, description="Service being paid for (optional).")


class VetVoucherCancel(BaseModel):
    """Request body for POST /api/vet-vouchers/{id}/cancel."""

    reason: str = Field(..., min_length=5, max_length=500, description="Reason for cancellation.")


class VetVoucherResponse(BaseModel):
    """Response for a single voucher."""

    id: UUID
    code: str
    amount_pyg: int
    amount_eur: float | None
    donor_id: UUID | None
    beneficiary_id: UUID | None
    clinic_id: UUID | None
    redeemed_clinic_id: UUID | None
    service_id: UUID | None
    service_category: str | None
    status: str
    purchased_at: datetime
    expires_at: datetime
    assigned_at: datetime | None
    redeemed_at: datetime | None
    cancelled_at: datetime | None
    notes: str | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VetVoucherListResponse(BaseModel):
    """Paginated response for listing vouchers."""

    items: list[VetVoucherResponse]
    total: int
    page: int
    page_size: int
