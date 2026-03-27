"""Pydantic schemas for Campaign resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.campaign import CampaignStatus, FundCategory
from src.db.models.donation import CurrencyCode

# Maximum number of additional photos per campaign
MAX_PHOTO_URLS = 10


class CampaignCreate(BaseModel):
    """Fields for creating a new campaign (admin only)."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    impact_story: str | None = None
    target_amount_cents: int = Field(..., gt=0)
    currency: CurrencyCode = CurrencyCode.EUR
    fund_category: FundCategory = FundCategory.GENERAL
    featured: bool = False
    image_url: str | None = Field(default=None, max_length=500)
    photo_urls: list[str] = Field(default_factory=list, max_length=MAX_PHOTO_URLS)
    deadline: datetime | None = None
    min_donation_cents: int | None = Field(default=None, gt=0)
    max_donation_cents: int | None = Field(default=None, gt=0)
    allow_overfunding: bool = True


class CampaignUpdate(BaseModel):
    """Fields for updating an existing campaign (admin only)."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    impact_story: str | None = None
    target_amount_cents: int | None = Field(default=None, gt=0)
    status: CampaignStatus | None = None
    featured: bool | None = None
    image_url: str | None = Field(default=None, max_length=500)
    photo_urls: list[str] | None = Field(default=None, max_length=MAX_PHOTO_URLS)
    deadline: datetime | None = None
    min_donation_cents: int | None = Field(default=None, gt=0)
    max_donation_cents: int | None = Field(default=None, gt=0)
    allow_overfunding: bool | None = None


class CampaignResponse(BaseModel):
    """Shape returned for a campaign record (admin view, full detail)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    impact_story: str | None
    target_amount_cents: int
    currency: CurrencyCode
    fund_category: FundCategory
    status: CampaignStatus
    featured: bool
    image_url: str | None
    photo_urls: list[str]
    deadline: datetime | None
    min_donation_cents: int | None
    max_donation_cents: int | None
    allow_overfunding: bool
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime


class CampaignPublicResponse(BaseModel):
    """Public campaign data with computed progress and time fields."""

    id: UUID
    title: str
    description: str
    impact_story: str | None
    target_amount_cents: int
    raised_amount_cents: int
    currency: CurrencyCode
    fund_category: FundCategory
    status: CampaignStatus
    featured: bool
    image_url: str | None
    photo_urls: list[str]
    deadline: datetime | None
    # Number of whole days remaining until deadline; None if no deadline set
    days_remaining: int | None
    min_donation_cents: int | None
    max_donation_cents: int | None
    allow_overfunding: bool
    donation_count: int
    progress_percentage: float
    created_at: datetime


class CampaignListResponse(BaseModel):
    """Paginated list of public campaigns."""

    items: list[CampaignPublicResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Social proof schemas (RAP-076)
# ---------------------------------------------------------------------------


class RecentDonorEntry(BaseModel):
    """A single donor entry shown on the campaign social proof panel.

    If the donor opted out of public listing, display_name is "Anonymous"
    and is_anonymous is True. The amount and timestamp are always shown.
    """

    display_name: str = Field(
        ...,
        description="Donor first name, or 'Anonymous' if opted out",
    )
    amount_cents: int = Field(..., description="Donation amount in smallest currency unit")
    currency: CurrencyCode
    donated_at: datetime = Field(..., description="When the donation was completed")
    is_anonymous: bool = Field(
        default=False,
        description="True when the donor opted out of public listing",
    )


class CampaignSocialProofResponse(BaseModel):
    """Social proof data for a campaign: donor counts, momentum, recent donors.

    Powers the campaign progress bar and social proof widgets on the public
    fundraising page — designed for high-frequency polling (cacheable).
    """

    campaign_id: UUID
    donor_count: int = Field(..., description="Total number of unique donors")
    total_raised_cents: int = Field(..., description="Sum of completed donations")
    currency: CurrencyCode
    progress_percentage: float = Field(
        ...,
        description="Percentage of goal raised (0.0-100.0+, capped at 100 if not overfunding)",
    )
    # Momentum metrics
    donations_last_24_hours: int = Field(
        ..., description="Number of completed donations in the past 24 hours"
    )
    donations_last_7_days: int = Field(
        ..., description="Number of completed donations in the past 7 days"
    )
    # Recent donor list for social proof — up to 10 entries, newest first
    recent_donors: list[RecentDonorEntry] = Field(
        default_factory=list,
        description="Last 10 completed donations, newest first",
    )
