"""Pydantic schemas for Email Template resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.email_template import TemplateStatus


class EmailTemplateCreate(BaseModel):
    """Fields for creating a new email template."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    subject: str = Field(..., min_length=1, max_length=500)
    html_body: str = Field(..., min_length=1)
    text_body: str | None = None


class EmailTemplateUpdate(BaseModel):
    """Fields for updating an existing email template."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    subject: str | None = Field(default=None, min_length=1, max_length=500)
    html_body: str | None = Field(default=None, min_length=1)
    text_body: str | None = None
    status: TemplateStatus | None = None


class EmailTemplateResponse(BaseModel):
    """Shape returned for an email template record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    subject: str
    html_body: str
    text_body: str | None
    status: str
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime


class EmailTemplateSummary(BaseModel):
    """Lightweight template summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    subject: str
    status: str
    created_at: datetime
