"""Centralized exception handlers for standardized error responses.

Registers handlers for:
  - RequestValidationError (422) — field-level validation errors
  - HTTPException — FastAPI HTTP errors (400, 401, 403, 404, 409, etc.)
  - RateLimitExceeded — 429 from slowapi
  - Exception — unhandled errors (500, no internal details leaked)
"""

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.schemas.error import ErrorDetail, ErrorResponse


def _make_request_id() -> str:
    """Generate a unique request identifier for log correlation."""
    return uuid.uuid4().hex[:12]


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error.get("loc", []))
            details.append(ErrorDetail(field=field, message=error.get("msg", "")))

        body = ErrorResponse(
            error_code="validation_error",
            message="Request validation failed",
            details=details,
            request_id=_make_request_id(),
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            409: "conflict",
            429: "rate_limit_exceeded",
            503: "service_unavailable",
        }
        error_code = error_code_map.get(exc.status_code, f"http_{exc.status_code}")

        body = ErrorResponse(
            error_code=error_code,
            message=str(exc.detail) if exc.detail else "An error occurred",
            request_id=_make_request_id(),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        body = ErrorResponse(
            error_code="rate_limit_exceeded",
            message="Too many requests. Please slow down.",
            request_id=_make_request_id(),
        )
        # Extract Retry-After from the exception if available
        retry_after = getattr(exc, "detail", "60")
        headers = {"Retry-After": str(retry_after)}
        return JSONResponse(status_code=429, content=body.model_dump(), headers=headers)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internal details in production
        body = ErrorResponse(
            error_code="internal_error",
            message="An unexpected error occurred",
            request_id=_make_request_id(),
        )
        return JSONResponse(status_code=500, content=body.model_dump())
