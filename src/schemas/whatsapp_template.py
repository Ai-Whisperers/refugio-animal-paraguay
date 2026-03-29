"""Pydantic schemas for WhatsApp message template endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

TemplateCategoryType = Literal["authentication", "marketing", "utility"]
TemplateStatusType = Literal["pending", "approved", "rejected", "paused", "deleted"]


class WhatsAppTemplateCreate(BaseModel):
    """Request body for POST /api/whatsapp/templates."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Template name as it will be registered in Meta Business Manager (lowercase, underscores only).",
    )
    language_code: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="BCP-47 language code (e.g. 'es', 'en', 'pt_BR').",
    )
    category: TemplateCategoryType = Field(
        ...,
        description="Meta template category: authentication | marketing | utility.",
    )
    header_text: str | None = Field(
        None,
        max_length=60,
        description="Optional header text (TEXT header type). Max 60 characters.",
    )
    body_text: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Template body with {{N}} variable placeholders. Max 1024 characters.",
    )
    footer_text: str | None = Field(
        None,
        max_length=60,
        description="Optional footer text. Max 60 characters.",
    )
    description: str | None = Field(
        None,
        max_length=500,
        description="Internal description for staff use (not sent to Meta).",
    )


class WhatsAppTemplateUpdate(BaseModel):
    """Request body for PATCH /api/whatsapp/templates/{template_id}."""

    status: TemplateStatusType | None = Field(
        None,
        description="Update approval status (e.g. after receiving Meta webhook).",
    )
    meta_template_id: str | None = Field(
        None,
        max_length=255,
        description="Template ID returned by Meta after submission.",
    )
    rejection_reason: str | None = Field(
        None,
        max_length=1000,
        description="Meta rejection reason (populated when status=rejected).",
    )
    header_text: str | None = Field(None, max_length=60)
    body_text: str | None = Field(None, min_length=1, max_length=1024)
    footer_text: str | None = Field(None, max_length=60)
    description: str | None = Field(None, max_length=500)
    is_active: bool | None = Field(None, description="Soft-archive this template.")
    approved_at: datetime | None = Field(
        None,
        description="Timestamp when Meta approved the template.",
    )


class WhatsAppTemplateResponse(BaseModel):
    """Response schema for a single WhatsApp template."""

    id: UUID
    name: str
    language_code: str
    category: str
    header_text: str | None
    body_text: str
    footer_text: str | None
    status: str
    meta_template_id: str | None
    rejection_reason: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None

    model_config = {"from_attributes": True}


class WhatsAppTemplateListResponse(BaseModel):
    """Paginated list of WhatsApp templates."""

    items: list[WhatsAppTemplateResponse]
    total: int
    page: int
    page_size: int
