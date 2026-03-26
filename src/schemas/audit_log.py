"""Pydantic schemas for audit log API requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Single audit log entry returned by the API."""

    id: int
    user_id: UUID
    action: str
    resource_type: str
    resource_id: str | None = None
    timestamp: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    http_method: str
    path: str
    status_code: int

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit log entries."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AuditLogFilter(BaseModel):
    """Query parameters for filtering audit logs."""

    user_id: UUID | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
