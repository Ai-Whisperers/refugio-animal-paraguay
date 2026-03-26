"""Pydantic schemas for the impact report generator."""

from datetime import datetime

from pydantic import BaseModel


class SpeciesCount(BaseModel):
    """Count of animals by species."""

    species: str
    count: int


class StatusCount(BaseModel):
    """Count of animals by status."""

    status: str
    count: int


class CurrencyTotal(BaseModel):
    """Donation total for a single currency."""

    currency: str
    total_cents: int
    donation_count: int


class InKindCategoryTotal(BaseModel):
    """In-kind donation total for a single category."""

    category: str
    count: int
    estimated_value_cents: int


class AnimalStats(BaseModel):
    """Aggregated animal statistics for the report period."""

    total_animals: int
    new_intakes: int
    by_species: list[SpeciesCount]
    by_status: list[StatusCount]


class AdoptionStats(BaseModel):
    """Aggregated adoption statistics for the report period."""

    total_requests: int
    approved: int
    rejected: int
    pending: int
    approval_rate_pct: float


class DonationStats(BaseModel):
    """Aggregated monetary donation statistics for the report period."""

    total_completed: int
    total_by_currency: list[CurrencyTotal]
    unique_donors: int


class InKindStats(BaseModel):
    """Aggregated in-kind donation statistics for the report period."""

    total_donations: int
    by_category: list[InKindCategoryTotal]


class ImpactReport(BaseModel):
    """Full shelter impact report for a date range."""

    report_title: str
    start_date: datetime
    end_date: datetime
    generated_at: datetime
    animals: AnimalStats
    adoptions: AdoptionStats
    donations: DonationStats
    in_kind: InKindStats
