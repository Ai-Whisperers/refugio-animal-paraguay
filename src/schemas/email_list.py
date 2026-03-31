"""Pydantic schemas for Email List management resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.db.models.email_list import EmailListStatus, EmailListType, MemberStatus


class EmailListCreate(BaseModel):
    """Fields for creating a new email list."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    list_type: EmailListType = EmailListType.GENERAL


class EmailListUpdate(BaseModel):
    """Fields for updating an existing email list."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: EmailListStatus | None = None


class EmailListResponse(BaseModel):
    """Shape returned for an email list record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    list_type: str
    status: str
    created_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
    subscriber_count: int


class EmailListSummary(BaseModel):
    """Lightweight email list summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    list_type: str
    status: str
    subscriber_count: int


class MemberAdd(BaseModel):
    """Request body for adding a subscriber to a list."""

    email: EmailStr
    name: str | None = Field(default=None, max_length=255)
    source_type: str | None = Field(
        default=None,
        description="Origin entity type: donor, adopter, volunteer, rescuer, manual",
    )
    source_id: UUID | None = None


class MemberResponse(BaseModel):
    """Shape returned for a list member record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email_list_id: UUID
    email: str
    name: str | None
    status: str
    source_type: str | None
    source_id: UUID | None
    subscribed_at: datetime
    unsubscribed_at: datetime | None


class MemberUpdate(BaseModel):
    """Fields for updating a member's status."""

    status: MemberStatus


class SegmentRequest(BaseModel):
    """Request to auto-populate a list from a segment type."""

    list_type: EmailListType = Field(
        ...,
        description="Segment type to import: donors, adopters, volunteers, etc.",
    )
    overwrite: bool = Field(
        default=False,
        description="If True, replace existing members. If False, append only new emails.",
    )


class SegmentResult(BaseModel):
    """Result of a segmentation import operation."""

    imported: int
    skipped: int
    total_after: int
