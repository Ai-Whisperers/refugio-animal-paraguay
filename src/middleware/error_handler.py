"""Centralized exception handlers for consistent API error responses.

Registers handlers for:
  - RequestValidationError (Pydantic validation failures -> 422)
  - HTTPException (FastAPI explicit errors -> various status codes)
  - RateLimitExceeded (slowapi rate limit -> 429)
  - IntegrityError (DB constraint violations -> 409)
  - stripe.StripeError (Stripe SDK errors -> 402/400/503/502)
  - Unhandled exceptions (catch-all -> 500)

All handlers return the standard ErrorResponse format.
"""

import logging
import uuid

import stripe
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from src.schemas.error import (
    ERROR_CARD_DECLINED,
    ERROR_CONFLICT,
    ERROR_INTERNAL,
    ERROR_INVALID_PAYMENT_PARAMS,
    ERROR_PAYMENT_SERVICE_UNAVAILABLE,
    ERROR_RATE_LIMITED,
    ERROR_VALIDATION,
    STATUS_TO_ERROR_CODE,
    ErrorResponse,
)

# ---------------------------------------------------------------------------
# Stripe card decline code → user-facing message mapping
#
# Maps Stripe card decline codes to user-friendly messages. Unknown codes
# fall back to the generic declined message.
# See: https://stripe.com/docs/declines/codes
# ---------------------------------------------------------------------------
_CARD_DECLINE_MESSAGES: dict[str, str] = {
    "insufficient_funds": "Insufficient funds. Please use a different card.",
    "expired_card": "Your card has expired. Please use a different card.",
    "incorrect_cvc": "Incorrect CVC code. Please check and try again.",
    "processing_error": "Card processing error. Please try again.",
    "lost_card": "Your card has been reported lost. Please use a different card.",
    "stolen_card": "Your card has been reported stolen. Please use a different card.",
    "do_not_honor": "Your card was declined. Please contact your bank.",
    "fraudulent": "Your card was declined. Please contact your bank.",
}

_CARD_DECLINED_GENERIC = "Your card was declined. Please try another card."

# ---------------------------------------------------------------------------
# Constraint name → human-readable message registry
#
# Maps PostgreSQL constraint names to user-facing messages returned in 409
# responses. Add entries here as new unique/FK constraints are created.
# ---------------------------------------------------------------------------
_CONSTRAINT_MESSAGES: dict[str, str] = {
    # Users
    "uq_users_email": "A user with this email already exists",
    # Adopters
    "uq_adopters_email": "An adopter with this email already exists",
    # Donors
    "uq_donors_email": "A donor with this email already exists",
    # Verification tokens
    "uq_verification_tokens_token": "Verification token conflict — please request a new token",
    # Sessions
    "uq_active_sessions_jti": "Session conflict — please log in again",
    # Consents
    "uq_user_consent_type": "Consent record already exists for this user and consent type",
    # Campaigns
    "uq_campaigns_slug": "A campaign with this slug already exists",
    # Animal updates (idempotency key)
    "uq_animal_updates_idempotency_key": "Duplicate animal update — this update has already been recorded",
}

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
    """Handle FastAPI HTTPExceptions with standard error format.

    Supports both string and dict-style detail. When detail is a dict with
    ``error_code`` and ``message`` keys, those values are used directly so
    that endpoints can pass domain-specific error codes through HTTPException.
    """
    headers = getattr(exc, "headers", None) or {}

    # Support structured detail: {"message": "...", "error_code": "..."}
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("error_code") or STATUS_TO_ERROR_CODE.get(
            exc.status_code, f"HTTP_{exc.status_code}"
        )
        message = exc.detail.get("message", str(exc.detail))
    else:
        error_code = STATUS_TO_ERROR_CODE.get(exc.status_code, f"HTTP_{exc.status_code}")
        message = str(exc.detail)

    return _build_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
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


def _extract_constraint_name(exc: IntegrityError) -> str | None:
    """Extract the constraint name from a SQLAlchemy IntegrityError.

    Works with both psycopg2 and asyncpg driver errors. Returns None if
    the constraint name cannot be determined.
    """
    orig = getattr(exc, "orig", None)
    if orig is None:
        return None

    # psycopg2: pgerror contains constraint name in 'DETAIL' or 'constraint "..."'
    pgerror: str = getattr(orig, "pgerror", "") or ""
    if "constraint" in pgerror.lower():
        import re

        match = re.search(r'constraint "([^"]+)"', pgerror)
        if match:
            return match.group(1)

    # asyncpg: ConstraintViolationError has a constraint_name attribute
    constraint_name = getattr(orig, "constraint_name", None)
    if constraint_name:
        return constraint_name

    # Fallback: diag attribute (psycopg2 diagnostics)
    diag = getattr(orig, "diag", None)
    if diag is not None:
        return getattr(diag, "constraint_name", None)

    return None


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """Handle SQLAlchemy IntegrityError (unique / FK / check constraint violations).

    Returns 409 CONFLICT for unique and foreign-key violations.
    Uses the constraint name registry to provide meaningful messages;
    falls back to a generic message when the constraint is unknown.
    """
    request_id = _get_request_id(request)

    # Log the full error internally for debugging
    logger.warning(
        "Database constraint violation: %s",
        type(exc.orig).__name__ if exc.orig else str(exc),
        extra={"request_id": request_id},
    )

    constraint_name = _extract_constraint_name(exc)
    message = (
        _CONSTRAINT_MESSAGES.get(constraint_name, "A resource conflict occurred")
        if constraint_name
        else "A resource conflict occurred"
    )

    return _build_error_response(
        status_code=409,
        error_code=ERROR_CONFLICT,
        message=message,
        request_id=request_id,
    )


async def stripe_error_handler(
    request: Request,
    exc: stripe.StripeError,
) -> JSONResponse:
    """Handle Stripe SDK exceptions with appropriate HTTP status codes.

    Maps Stripe error types to user-safe responses without leaking credentials
    or internal Stripe details.

    Mapping:
      CardError             → 402 CARD_DECLINED (with decline-code-specific message)
      AuthenticationError   → 503 PAYMENT_SERVICE_UNAVAILABLE (logged at ERROR)
      RateLimitError        → 503 RATE_LIMITED (with Retry-After: 60)
      InvalidRequestError   → 400 INVALID_PAYMENT_PARAMS
      APIConnectionError    → 503 PAYMENT_SERVICE_UNAVAILABLE
      StripeError (generic) → 502 PAYMENT_SERVICE_UNAVAILABLE
    """
    request_id = _get_request_id(request)

    if isinstance(exc, stripe.CardError):
        decline_code: str = getattr(exc, "code", "") or ""
        message = _CARD_DECLINE_MESSAGES.get(decline_code, _CARD_DECLINED_GENERIC)
        logger.warning(
            "Stripe card declined: decline_code=%s",
            decline_code,
            extra={"request_id": request_id},
        )
        return _build_error_response(
            status_code=402,
            error_code=ERROR_CARD_DECLINED,
            message=message,
            request_id=request_id,
        )

    if isinstance(exc, stripe.AuthenticationError):
        logger.error(
            "Stripe authentication error — check STRIPE_SECRET_KEY",
            extra={"request_id": request_id},
        )
        return _build_error_response(
            status_code=503,
            error_code=ERROR_PAYMENT_SERVICE_UNAVAILABLE,
            message="Payment service unavailable. Please try again later.",
            request_id=request_id,
        )

    if isinstance(exc, stripe.RateLimitError):
        logger.warning(
            "Stripe rate limit exceeded",
            extra={"request_id": request_id},
        )
        return _build_error_response(
            status_code=503,
            error_code=ERROR_RATE_LIMITED,
            message="Service temporarily overwhelmed. Please retry in 60 seconds.",
            request_id=request_id,
            headers={"Retry-After": "60"},
        )

    if isinstance(exc, stripe.InvalidRequestError):
        logger.error(
            "Stripe invalid request: %s",
            str(exc),
            extra={"request_id": request_id},
        )
        return _build_error_response(
            status_code=400,
            error_code=ERROR_INVALID_PAYMENT_PARAMS,
            message="Invalid payment parameters.",
            request_id=request_id,
        )

    if isinstance(exc, stripe.APIConnectionError):
        logger.error(
            "Stripe API connection error: %s",
            type(exc).__name__,
            extra={"request_id": request_id},
        )
        return _build_error_response(
            status_code=503,
            error_code=ERROR_PAYMENT_SERVICE_UNAVAILABLE,
            message="Payment service unavailable. Please try again.",
            request_id=request_id,
        )

    # Generic StripeError fallback
    logger.error(
        "Stripe error: %s",
        type(exc).__name__,
        extra={"request_id": request_id},
    )
    return _build_error_response(
        status_code=502,
        error_code=ERROR_PAYMENT_SERVICE_UNAVAILABLE,
        message="Payment service error. Please try again.",
        request_id=request_id,
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
    # IntegrityError must be registered before the generic Exception handler
    app.add_exception_handler(IntegrityError, integrity_error_handler)  # type: ignore[arg-type]
    # StripeError must be registered before the generic Exception handler
    app.add_exception_handler(stripe.StripeError, stripe_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)  # type: ignore[arg-type]
