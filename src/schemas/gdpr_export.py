"""Pydantic schemas for GDPR data export endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DataExportCreateRequest(BaseModel):
    """Request to create a GDPR data export."""

    subject_type: str = Field(
        ...,
        pattern="^(donor|adopter|staff)$",
        description="Type of data subject: donor, adopter, or staff",
    )
    subject_id: UUID = Field(
        ...,
        description="ID of the data subject (donor_id, adopter_id, or user_id)",
    )
    subject_email: str = Field(
        ...,
        max_length=255,
        description="Email of the data subject (for audit trail)",
    )


class DataExportResponse(BaseModel):
    """Response for a data export request (without the export data itself)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requested_by_user_id: UUID | None = None
    subject_type: str
    subject_id: UUID
    subject_email: str
    status: str
    error_message: str | None = None
    requested_at: datetime
    completed_at: datetime | None = None
    downloaded_at: datetime | None = None
    expires_at: datetime | None = None


class DataExportDownloadResponse(BaseModel):
    """Response for downloading export data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_type: str
    subject_email: str
    status: str
    export_data: dict | None = None
    downloaded_at: datetime | None = None


class DataExportListResponse(BaseModel):
    """Paginated list of export requests."""

    items: list[DataExportResponse]
    count: int
