"""Pydantic schemas for campaign endpoints."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CampaignCreateRequest(BaseModel):
    """Request to create a new campaign."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    goal_amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^(USD|EUR)$")
    category: str = Field(
        default="other",
        pattern="^(medical|food|operations|rescue|facility|other)$",
    )
    deadline: date | None = None
    featured: bool = False


class CampaignUpdateRequest(BaseModel):
    """Request to update a campaign."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    goal_amount_cents: int | None = Field(default=None, gt=0)
    category: str | None = Field(
        default=None,
        pattern="^(medical|food|operations|rescue|facility|other)$",
    )
    status: str | None = Field(
        default=None,
        pattern="^(draft|active|paused|completed|archived)$",
    )
    deadline: date | None = None
    featured: bool | None = None


class CampaignResponse(BaseModel):
    """Full campaign detail with progress."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    goal_amount_cents: int
    currency: str
    category: str
    status: str
    featured: bool
    deadline: date | None = None
    created_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    # Computed fields added by the service
    raised_amount_cents: int = 0
    progress_pct: float = 0.0
    donor_count: int = 0


class CampaignListResponse(BaseModel):
    """Paginated list of campaigns."""

    items: list[CampaignResponse]
    count: int
