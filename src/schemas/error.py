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
ERROR_BAD_GATEWAY = "BAD_GATEWAY"
ERROR_SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

# Payment-specific error codes
ERROR_CARD_DECLINED = "CARD_DECLINED"
ERROR_PAYMENT_SERVICE_UNAVAILABLE = "PAYMENT_SERVICE_UNAVAILABLE"
ERROR_INVALID_PAYMENT_PARAMS = "INVALID_PAYMENT_PARAMS"
ERROR_WEBHOOK_VERIFICATION_FAILED = "WEBHOOK_VERIFICATION_FAILED"
ERROR_INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"

# HTTP status code to error code mapping
STATUS_TO_ERROR_CODE: dict[int, str] = {
    400: ERROR_BAD_REQUEST,
    401: ERROR_UNAUTHORIZED,
    403: ERROR_FORBIDDEN,
    404: ERROR_NOT_FOUND,
    409: ERROR_CONFLICT,
    422: ERROR_VALIDATION,
    429: ERROR_RATE_LIMITED,
    502: ERROR_BAD_GATEWAY,
    503: ERROR_SERVICE_UNAVAILABLE,
}

# Pre-built OpenAPI response dicts for router `responses=` parameters.
# Usage:
#   router = APIRouter(prefix="/...", responses=COMMON_RESPONSES)
#   @router.get("/{id}", responses={**AUTHENTICATED_RESPONSES, 409: _conflict})
_not_found = {"description": "Resource not found", "model": ErrorResponse}
_unprocessable = {"description": "Validation error", "model": ErrorResponse}
_unauthorized = {"description": "Authentication required", "model": ErrorResponse}
_forbidden = {"description": "Permission denied", "model": ErrorResponse}
_conflict = {"description": "Conflict with existing resource", "model": ErrorResponse}
_internal = {"description": "Unexpected server error", "model": ErrorResponse}
_bad_gateway = {"description": "External service error", "model": ErrorResponse}
_service_unavailable = {"description": "Service temporarily unavailable", "model": ErrorResponse}

# Responses applicable to all public endpoints
COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: _unprocessable,
    500: _internal,
}

# Responses applicable to authenticated endpoints
AUTHENTICATED_RESPONSES: dict[int | str, dict[str, Any]] = {
    **COMMON_RESPONSES,
    401: _unauthorized,
    403: _forbidden,
}

# Responses for endpoints that fetch by ID
RESOURCE_RESPONSES: dict[int | str, dict[str, Any]] = {
    **AUTHENTICATED_RESPONSES,
    404: _not_found,
}

# Responses for payment-related endpoints (may call external gateways)
PAYMENT_RESPONSES: dict[int | str, dict[str, Any]] = {
    **AUTHENTICATED_RESPONSES,
    404: _not_found,
    409: _conflict,
    502: _bad_gateway,
    503: _service_unavailable,
}
