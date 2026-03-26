"""Standardized error response schemas.

All API errors follow this format for consistent frontend consumption.
"""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Field-level validation error detail."""

    field: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response returned by all API error handlers.

    Attributes:
        error_code: Machine-readable error identifier (e.g., "validation_error").
        message: Human-readable error description.
        details: Optional list of field-level errors (for 422 responses).
        request_id: Unique request identifier for log correlation.
    """

    error_code: str
    message: str
    details: list[ErrorDetail] | None = Field(default=None)
    request_id: str | None = Field(default=None)
