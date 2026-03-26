"""Centralised exception handlers for the FastAPI application.

Converts all exceptions into the standard ErrorResponse format.
Handlers are registered via register_error_handlers(app) in the app factory.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.schemas.error import ErrorResponse, ValidationErrorDetail

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Extract request ID set by RequestIDMiddleware, if available."""
    return getattr(request.state, "request_id", None)


def _build_response(
    status_code: int,
    error_code: str,
    message: str,
    request: Request,
    details: list[ValidationErrorDetail] | dict | None = None,  # type: ignore[type-arg]
) -> JSONResponse:
    """Build a standard JSON error response."""
    body = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        request_id=_get_request_id(request),
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """422 — Pydantic/FastAPI validation errors with field-level details."""
    details = [
        ValidationErrorDetail(
            field=".".join(str(loc) for loc in err.get("loc", ())),
            message=err.get("msg", "Validation error"),
            type=err.get("type", "value_error"),
        )
        for err in exc.errors()
    ]
    return _build_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="validation_error",
        message="Request validation failed",
        request=request,
        details=details,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """4xx/5xx — FastAPI/Starlette HTTPException."""
    error_code = _status_to_error_code(exc.status_code)
    return _build_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail) if exc.detail else error_code,
        request=request,
    )


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """429 — Rate limit exceeded."""
    # Extract retry-after from the exception message (slowapi format: "N per M period")
    retry_after = _parse_retry_after(str(exc.detail))
    response = _build_response(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        error_code="rate_limit_exceeded",
        message="Too many requests. Please slow down.",
        request=request,
        details={"retry_after_seconds": retry_after},
    )
    response.headers["Retry-After"] = str(retry_after)
    return response


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """500 — Catch-all for unhandled exceptions.

    Logs the full traceback but returns a generic message to the client
    to prevent leaking internal details.
    """
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
        extra={"request_id": _get_request_id(request)},
    )
    return _build_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="internal_error",
        message="An unexpected error occurred. Please try again later.",
        request=request,
    )


def _status_to_error_code(status_code: int) -> str:
    """Map HTTP status codes to machine-readable error codes."""
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_error",
        502: "bad_gateway",
        503: "service_unavailable",
    }
    return mapping.get(status_code, f"http_{status_code}")


_DEFAULT_RETRY_AFTER_SECONDS = 60


def _parse_retry_after(detail: str) -> int:
    """Parse slowapi rate limit detail to extract a retry-after value in seconds.

    slowapi details look like "Rate limit exceeded: 5 per 1 minute".
    Returns a sensible default of 60 if parsing fails.
    """
    try:
        # Try to extract the period from "N per M period" format
        if "minute" in detail:
            return 60
        if "second" in detail:
            return 1
        if "hour" in detail:
            return 3600
    except (ValueError, IndexError):
        pass
    return _DEFAULT_RETRY_AFTER_SECONDS


def register_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app.

    Call this in the app factory after creating the app instance.
    """
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
