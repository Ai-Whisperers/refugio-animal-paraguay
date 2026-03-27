"""Pydantic schemas for audit trail API.

Includes response models for audit log entries and query parameter
models for filtering and pagination.
"""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AuditLogResponse(BaseModel):
    """Single audit log entry returned by the API."""

    id: UUID
    user_id: UUID
    action: str
    resource_type: str
    resource_id: str | None = None
    timestamp: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    old_values: dict | None = None
    new_values: dict | None = None
    request_id: str | None = None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit log entries."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


# Query parameter defaults
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


MAX_ACTION_LENGTH = 100
MAX_RESOURCE_TYPE_LENGTH = 100
MAX_RESOURCE_ID_LENGTH = 255


class AuditLogFilters(BaseModel):
    """Query filters for audit log listing."""

    user_id: UUID | None = None
    action: str | None = Field(default=None, max_length=MAX_ACTION_LENGTH)
    resource_type: str | None = Field(default=None, max_length=MAX_RESOURCE_TYPE_LENGTH)
    resource_id: str | None = Field(default=None, max_length=MAX_RESOURCE_ID_LENGTH)
    start_date: datetime | None = None
    end_date: datetime | None = None
    page: int = Field(default=DEFAULT_PAGE, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)

    @model_validator(mode="after")
    def end_date_not_before_start_date(self) -> Self:
        """Reject date ranges where end_date precedes start_date."""
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must not be before start_date")
        return self
