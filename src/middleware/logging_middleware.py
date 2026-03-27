"""Request/response logging middleware.

Logs every HTTP request with method, path, status code, duration, user identity,
request ID, and response size. Integrates with the structlog pipeline configured
in src/logging_config.py (RAP-415) when available; falls back to stdlib logging
transparently.

Excluded paths (never logged — would clutter logs or expose sensitive info):
  /health, /docs, /redoc, /openapi.json, /static/*

Log levels:
  INFO    — normal requests (status < 500, duration ≤ 1000 ms)
  WARNING — slow requests (duration > 1000 ms, status < 500)
  ERROR   — server error responses (status >= 500)
"""

import contextlib
import logging
import time
from collections.abc import Awaitable, Callable

from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.auth.utils import decode_access_token
from src.config import get_settings

logger = logging.getLogger(__name__)

# Paths excluded from access logging — noisy or sensitive.
_EXCLUDED_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    }
)

# Requests slower than this threshold are logged at WARNING.
_SLOW_REQUEST_THRESHOLD_MS: int = 1000

# Response bodies larger than this are flagged at WARNING.
_LARGE_RESPONSE_THRESHOLD_BYTES: int = 1_000_000


def _extract_user_id(request: Request) -> str | None:
    """Extract user ID from a Bearer JWT without touching the database.

    Returns the ``sub`` claim if the token is valid and present; None otherwise.
    Does not raise — any error results in None (unauthenticated or bad token).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[len("Bearer ") :]
    try:
        settings = get_settings()
        payload = decode_access_token(
            token,
            secret_key=settings.secret_key,
            algorithm=settings.algorithm,
        )
        return str(payload.get("sub")) if payload.get("sub") else None
    except (JWTError, Exception):
        return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every non-excluded HTTP request with timing and context fields.

    Attaches ``user_id`` extracted from JWT (if present) to ``request.state``
    so downstream handlers can reference it without re-decoding the token.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Time and log the request/response cycle."""
        path = request.url.path

        # Skip excluded paths entirely — no logging overhead.
        if path in _EXCLUDED_PATHS or path.startswith("/static/"):
            return await call_next(request)

        # Decode user identity once; store on state for downstream handlers.
        user_id = _extract_user_id(request)
        request.state.user_id = user_id

        request_id: str = getattr(request.state, "request_id", "")

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start) * 1000)

        status_code = response.status_code
        response_size: int | None = None
        content_length = response.headers.get("content-length")
        if content_length is not None:
            with contextlib.suppress(ValueError):
                response_size = int(content_length)

        log_fields: dict[str, object] = {
            "method": request.method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "request_id": request_id,
        }
        if response_size is not None:
            log_fields["response_size_bytes"] = response_size

        if status_code >= 500:
            logger.error("http_request", extra=log_fields)
        elif duration_ms > _SLOW_REQUEST_THRESHOLD_MS:
            logger.warning("http_request_slow", extra=log_fields)
        else:
            logger.info("http_request", extra=log_fields)

        if response_size is not None and response_size > _LARGE_RESPONSE_THRESHOLD_BYTES:
            logger.warning(
                "http_large_response",
                extra={
                    "path": path,
                    "response_size_bytes": response_size,
                    "request_id": request_id,
                },
            )

        return response
