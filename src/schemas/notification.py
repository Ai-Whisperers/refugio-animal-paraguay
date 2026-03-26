"""Pydantic schemas for in-app notifications API."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Single notification in API responses."""

    id: UUID
    user_id: UUID
    notification_type: str
    title: str
    message: str
    data: dict | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationResponse]
    total: int
    offset: int
    limit: int


class UnreadCountResponse(BaseModel):
    """Unread notification count."""

    unread_count: int


class MarkAllReadResponse(BaseModel):
    """Result of marking all notifications as read."""

    marked_count: int


class NotificationCreateRequest(BaseModel):
    """Request to create a notification (admin/system use)."""

    user_id: UUID
    notification_type: str = Field(
        ...,
        pattern="^(adoption_request_created|adoption_status_changed|"
        "donation_received|donation_refunded|"
        "animal_intake_completed|animal_status_changed|"
        "system_alert|gdpr_request)$",
    )
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    data: dict | None = None
