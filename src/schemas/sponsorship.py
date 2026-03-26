"""Pydantic schemas for sponsorship endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SponsorshipCreateRequest(BaseModel):
    """Request to create a new animal sponsorship."""

    donor_id: UUID
    animal_id: UUID
    tier: str = Field(..., pattern="^(bronze|silver|gold)$")
    currency: str = Field(default="USD", pattern="^(USD|EUR)$")
    interval: str = Field(default="month", pattern="^(month|year)$")


class SponsorshipUpdateRequest(BaseModel):
    """Request to update a sponsorship (change tier, pause, resume)."""

    tier: str | None = Field(default=None, pattern="^(bronze|silver|gold)$")
    action: str | None = Field(default=None, pattern="^(pause|resume)$")


class SponsorshipResponse(BaseModel):
    """Full sponsorship detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donor_id: UUID
    animal_id: UUID
    tier: str
    amount_cents: int
    currency: str
    interval: str
    status: str
    stripe_subscription_id: str | None = None
    started_at: datetime
    paused_at: datetime | None = None
    cancelled_at: datetime | None = None
    current_period_end: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SponsorshipListResponse(BaseModel):
    """List of sponsorships for a donor or animal."""

    items: list[SponsorshipResponse]
    count: int
