"""Standardized error response schemas.

All API errors return an ErrorResponse body with a consistent structure:
  - error_code: machine-readable error identifier (e.g. "validation_error")
  - message: human-readable description
  - details: optional field-level or contextual details
  - request_id: unique ID for tracing (set by request-ID middleware)
"""

from typing import Any

from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """Field-level validation error detail."""

    field: str = Field(description="Dot-path to the invalid field (e.g. 'body.email')")
    message: str = Field(description="What is wrong with this field")
    type: str = Field(description="Validation error type (e.g. 'value_error', 'missing')")


class ErrorResponse(BaseModel):
    """Standard error response returned by all API error handlers.

    Clients can rely on this shape for all 4xx and 5xx responses.
    """

    error_code: str = Field(description="Machine-readable error code (e.g. 'not_found')")
    message: str = Field(description="Human-readable error description")
    details: list[ValidationErrorDetail] | dict[str, Any] | None = Field(
        default=None,
        description="Optional structured details (field errors for 422, context for others)",
    )
    request_id: str | None = Field(
        default=None,
        description="Unique request identifier for log correlation",
    )
