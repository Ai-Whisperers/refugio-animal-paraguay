"""Pydantic v2 schemas for sponsorship tiers and sponsorships."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.db.models.sponsorship import SponsorshipFrequency, SponsorshipStatus, SponsorshipTierLevel

# ---------------------------------------------------------------------------
# SponsorshipTier schemas
# ---------------------------------------------------------------------------


class SponsorshipTierResponse(BaseModel):
    """Serialized sponsorship tier for API responses."""

    id: UUID
    level: SponsorshipTierLevel
    name: str
    amount_cents: int
    currency: str
    benefits: dict | None
    active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SponsorshipTierUpdate(BaseModel):
    """Staff-only partial update for a sponsorship tier (Stripe price IDs, benefits)."""

    stripe_price_id_monthly: str | None = None
    stripe_price_id_annual: str | None = None
    benefits: dict | None = None
    active: bool | None = None


# ---------------------------------------------------------------------------
# Sponsorship schemas
# ---------------------------------------------------------------------------


class SponsorshipCreate(BaseModel):
    """Payload to create a new sponsorship."""

    donor_id: UUID
    animal_id: UUID
    tier_level: SponsorshipTierLevel = Field(
        ...,
        description="Tier level: bronze, silver, or gold",
    )
    frequency: SponsorshipFrequency = SponsorshipFrequency.MONTHLY
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def notes_max_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 1000:
            raise ValueError("notes must be 1000 characters or fewer")
        return v


class SponsorshipResponse(BaseModel):
    """Serialized sponsorship for API responses."""

    id: UUID
    donor_id: UUID
    animal_id: UUID
    tier_id: UUID
    frequency: SponsorshipFrequency
    status: SponsorshipStatus
    stripe_subscription_id: str | None
    total_contributed_cents: int
    started_at: datetime
    ended_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    # Nested tier for convenience
    tier: SponsorshipTierResponse | None = None

    model_config = {"from_attributes": True}


class SponsorshipListResponse(BaseModel):
    """Paginated list of sponsorships."""

    items: list[SponsorshipResponse]
    total: int
    page: int
    page_size: int


class SponsorshipCancelRequest(BaseModel):
    """Optional payload when cancelling a sponsorship."""

    notes: str | None = Field(None, max_length=1000)


class SponsorshipPauseRequest(BaseModel):
    """Optional payload when pausing a sponsorship."""

    notes: str | None = Field(None, max_length=1000)
