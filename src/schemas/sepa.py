"""Pydantic schemas for SEPA Direct Debit operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SepaSetupRequest(BaseModel):
    """Request to set up a SEPA Direct Debit mandate for a donor."""

    donor_id: UUID
    iban: str = Field(..., min_length=15, max_length=34, description="Donor's IBAN")
    amount_cents: int = Field(..., gt=0, description="Recurring donation amount in EUR cents")
    interval: str = Field(
        default="month",
        pattern="^(month|year)$",
        description="Debit interval: month or year",
    )


class SepaSetupResponse(BaseModel):
    """Response after creating a SEPA SetupIntent — contains client_secret for frontend."""

    mandate_id: UUID
    donor_id: UUID
    stripe_setup_intent_id: str
    client_secret: str
    amount_cents: int
    interval: str


class SepaMandateResponse(BaseModel):
    """Full SEPA mandate record for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donor_id: UUID
    stripe_customer_id: str
    stripe_setup_intent_id: str | None
    stripe_payment_method_id: str | None
    stripe_mandate_id: str | None
    iban_last4: str | None
    status: str
    amount_cents: int
    interval: str
    stripe_subscription_id: str | None
    activated_at: datetime | None
    revoked_at: datetime | None
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime


class SepaMandateListResponse(BaseModel):
    """List of mandates for a donor."""

    donor_id: UUID
    mandates: list[SepaMandateResponse]
