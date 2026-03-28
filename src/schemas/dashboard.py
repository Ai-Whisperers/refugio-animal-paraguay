"""Pydantic response schemas for the portal dashboard."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApplicationItem(BaseModel):
    """Single adoption application summary."""

    id: UUID
    animal_name: str
    animal_species: str
    submitted_at: datetime
    status: str = Field(description="pending | approved | rejected | cancelled")


class DonationStats(BaseModel):
    """Aggregated donation summary."""

    total_count: int = Field(ge=0)
    total_amount_cents: int = Field(ge=0, description="Total donated in smallest currency unit")
    currency: str = Field(description="Preferred currency code (EUR, PYG, USD)")
    last_donation_at: datetime | None = None


class SponsoredAnimalItem(BaseModel):
    """Single sponsored animal summary."""

    animal_id: UUID
    animal_name: str
    animal_species: str
    tier_name: str
    frequency: str = Field(description="monthly | annual")
    status: str = Field(description="active | paused")


class DashboardResponse(BaseModel):
    """Complete dashboard payload returned by GET /api/portal/dashboard."""

    user_id: UUID
    display_name: str
    email: str
    role: str
    applications: list[ApplicationItem] = Field(default_factory=list)
    donation_summary: DonationStats
    sponsored_animals: list[SponsoredAnimalItem] = Field(default_factory=list)
    # Convenience counts for quick-access cards
    total_applications: int = Field(ge=0)
    total_sponsored_animals: int = Field(ge=0)
