"""Standardized error response schemas.

All API errors return this format for consistency:
  {
    "error_code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [...field-level errors...],
    "request_id": "uuid"
  }
"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Field-level error detail for validation errors."""

    field: str = Field(..., description="The field that caused the error")
    message: str = Field(..., description="Human-readable error description")
    type: str = Field(..., description="Error type identifier")


class ErrorResponse(BaseModel):
    """Standard error response returned by all API error handlers."""

    error_code: str = Field(..., description="Machine-readable error code (e.g. VALIDATION_ERROR)")
    message: str = Field(..., description="Human-readable error description")
    details: list[Any] = Field(
        default_factory=list,
        description="Additional error details (field-level for validation errors)",
    )
    request_id: str | None = Field(
        default=None,
        description="Unique request identifier for tracing",
    )


# Standard error codes
ERROR_VALIDATION = "VALIDATION_ERROR"
ERROR_NOT_FOUND = "NOT_FOUND"
ERROR_UNAUTHORIZED = "UNAUTHORIZED"
ERROR_FORBIDDEN = "FORBIDDEN"
ERROR_CONFLICT = "CONFLICT"
ERROR_RATE_LIMITED = "RATE_LIMITED"
ERROR_BAD_REQUEST = "BAD_REQUEST"
ERROR_INTERNAL = "INTERNAL_ERROR"

# HTTP status code to error code mapping
STATUS_TO_ERROR_CODE: dict[int, str] = {
    400: ERROR_BAD_REQUEST,
    401: ERROR_UNAUTHORIZED,
    403: ERROR_FORBIDDEN,
    404: ERROR_NOT_FOUND,
    409: ERROR_CONFLICT,
    422: ERROR_VALIDATION,
    429: ERROR_RATE_LIMITED,
}
