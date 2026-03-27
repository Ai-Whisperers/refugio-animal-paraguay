"""Pydantic schemas for animal update notifications."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnimalUpdateCreate(BaseModel):
    """Request body to publish a new animal update."""

    animal_id: UUID = Field(..., description="Animal this update is about")
    title: str = Field(..., min_length=3, max_length=255, description="Short update title")
    content: str = Field(..., min_length=10, description="Full update text")
    update_type: str = Field(
        default="general",
        description="health | behavior | milestone | general",
    )
    milestone_type: str | None = Field(
        default=None,
        description="Required when update_type=milestone. vaccination | birthday | etc.",
    )
    photo_urls: list[str] = Field(
        default_factory=list,
        description="List of photo URLs attached to this update",
    )


class AnimalUpdateResponse(BaseModel):
    """Animal update as returned by the API."""

    id: UUID
    animal_id: UUID
    published_by_user_id: UUID | None
    title: str
    content: str
    update_type: str
    milestone_type: str | None
    photo_urls: list[str]
    published_at: datetime
    sponsors_notified: int = Field(
        default=0,
        description="Number of sponsors notified when this update was published",
    )

    model_config = {"from_attributes": True}


class SponsorUpdatePreferenceUpdate(BaseModel):
    """Request to update a sponsor's notification preference for a sponsorship."""

    notification_enabled: bool = Field(
        default=True,
        description="Whether to receive notifications for this sponsored animal",
    )
    notification_frequency: str = Field(
        default="immediate",
        description="immediate | daily_digest | weekly_digest | monthly_digest",
    )


class SponsorUpdatePreferenceResponse(BaseModel):
    """Current notification preference for a sponsorship."""

    id: UUID
    sponsorship_id: UUID
    notification_enabled: bool
    notification_frequency: str

    model_config = {"from_attributes": True}
