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
