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
    # A/B testing — both subject lines must be provided together
    subject_a: str | None = Field(
        default=None,
        max_length=255,
        description="Subject line for variant A. Required when subject_b is set.",
    )
    subject_b: str | None = Field(
        default=None,
        max_length=255,
        description="Subject line for variant B. When set, A/B test mode is active.",
    )
    ab_ratio: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Fraction of recipients assigned to variant A (0.0-1.0).",
    )


class EmailCampaignUpdate(BaseModel):
    """Fields for updating a draft campaign."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    email_list_id: UUID | None = None
    email_template_id: UUID | None = None
    scheduled_at: datetime | None = None
    status: EmailCampaignStatus | None = None
    subject_a: str | None = Field(default=None, max_length=255)
    subject_b: str | None = Field(default=None, max_length=255)
    ab_ratio: float | None = Field(default=None, ge=0.0, le=1.0)


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
    subject_a: str | None
    subject_b: str | None
    ab_ratio: float | None


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
    subject_b: str | None
