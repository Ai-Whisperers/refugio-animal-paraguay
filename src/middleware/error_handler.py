"""Centralized exception handlers for consistent API error responses.

Registers handlers for:
  - RequestValidationError (Pydantic validation failures -> 422)
  - HTTPException (FastAPI explicit errors -> various status codes)
  - RateLimitExceeded (slowapi rate limit -> 429)
  - Unhandled exceptions (catch-all -> 500)

All handlers return the standard ErrorResponse format.
"""

import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.schemas.error import (
    ERROR_INTERNAL,
    ERROR_RATE_LIMITED,
    ERROR_VALIDATION,
    STATUS_TO_ERROR_CODE,
    ErrorResponse,
)

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str:
    """Extract request ID from state (set by RequestIDMiddleware) or generate a new one."""
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def _build_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: list | None = None,
    request_id: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build a standardized JSON error response."""
    body = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details or [],
        request_id=request_id or str(uuid.uuid4()),
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers=headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors with field-level details."""
    details = []
    for error in exc.errors():
        loc = error.get("loc", ())
        field_path = " -> ".join(str(loc_part) for loc_part in loc)
        details.append(
            {
                "field": field_path,
                "message": error.get("msg", str(error.get("type", "Unknown error"))),
                "type": str(error.get("type", "unknown")),
            }
        )

    return _build_error_response(
        status_code=422,
        error_code=ERROR_VALIDATION,
        message="Request validation failed",
        details=details,
        request_id=_get_request_id(request),
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Handle FastAPI HTTPExceptions with standard error format."""
    error_code = STATUS_TO_ERROR_CODE.get(exc.status_code, f"HTTP_{exc.status_code}")
    headers = getattr(exc, "headers", None) or {}

    return _build_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail),
        request_id=_get_request_id(request),
        headers=headers if headers else None,
    )


async def rate_limit_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """Handle rate limit exceeded errors with Retry-After header."""
    # Extract retry-after from the exception's response headers if available
    retry_after = "60"
    if hasattr(exc, "detail") and exc.detail:
        retry_after_value = getattr(exc, "retry_after", None)
        if retry_after_value:
            retry_after = str(retry_after_value)

    return _build_error_response(
        status_code=429,
        error_code=ERROR_RATE_LIMITED,
        message="Rate limit exceeded. Please retry later.",
        request_id=_get_request_id(request),
        headers={"Retry-After": retry_after},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for unhandled exceptions. Never leaks internal details."""
    logger.exception("Unhandled exception: %s", type(exc).__name__)

    return _build_error_response(
        status_code=500,
        error_code=ERROR_INTERNAL,
        message="An unexpected error occurred",
        request_id=_get_request_id(request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
