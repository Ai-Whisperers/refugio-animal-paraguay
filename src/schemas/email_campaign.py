"""Pydantic schemas for Email Campaign resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.email_campaign import EmailCampaignStatus


class EmailCampaignCreate(BaseModel):
    """Fields for creating a new email campaign."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    email_list_id: UUID
    email_template_id: UUID
    scheduled_at: datetime | None = Field(
        default=None,
        description="When to send the campaign. If null, campaign must be triggered manually.",
    )


class EmailCampaignUpdate(BaseModel):
    """Fields for updating a draft campaign."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    email_list_id: UUID | None = None
    email_template_id: UUID | None = None
    scheduled_at: datetime | None = None
    status: EmailCampaignStatus | None = None


class EmailCampaignResponse(BaseModel):
    """Shape returned for an email campaign record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    email_list_id: UUID
    email_template_id: UUID
    status: str
    scheduled_at: datetime | None
    sent_at: datetime | None
    sent_count: int
    failed_count: int
    total_recipients: int
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
    error_message: str | None


class EmailCampaignSummary(BaseModel):
    """Lightweight campaign summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    email_list_id: UUID
    email_template_id: UUID
    scheduled_at: datetime | None
    sent_count: int
    total_recipients: int
    created_at: datetime
