"""Pydantic schemas for GDPR data deletion endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeletionRequestCreate(BaseModel):
    """Request to create a GDPR deletion request."""

    subject_type: str = Field(
        ...,
        pattern="^(donor|adopter|staff)$",
        description="Type of data subject: donor, adopter, or staff",
    )
    subject_id: UUID = Field(
        ...,
        description="ID of the data subject",
    )
    subject_email: str = Field(
        ...,
        max_length=255,
        description="Email of the data subject (for audit trail)",
    )
    reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional reason for the deletion request",
    )


class DeletionRequestApproval(BaseModel):
    """Approval action for a deletion request."""

    # No fields needed — approval is just a POST by an admin


class DeletionRequestDenial(BaseModel):
    """Denial action for a deletion request."""

    denial_reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional reason for denying the request",
    )


class DeletionRequestResponse(BaseModel):
    """Response for a deletion request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_type: str
    subject_id: UUID
    subject_email: str
    reason: str | None = None
    status: str
    requested_by_user_id: UUID | None = None
    approved_by_user_id: UUID | None = None
    denial_reason: str | None = None
    requested_at: datetime
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    cancelled_at: datetime | None = None


class DeletionRequestListResponse(BaseModel):
    """List of deletion requests."""

    items: list[DeletionRequestResponse]
    count: int
