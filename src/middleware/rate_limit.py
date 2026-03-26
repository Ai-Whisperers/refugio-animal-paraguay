"""Rate limiting middleware using slowapi.

Provides two rate limit tiers:
  - AUTH_RATE_LIMIT: strict limit for auth endpoints (default: 5/minute)
  - DEFAULT_RATE_LIMIT: general limit for all endpoints (default: 60/minute)

Rate limiting can be toggled off via RATE_LIMIT_ENABLED=false in settings.
When disabled, the limiter is still attached but uses a permissive limit.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import Response

AUTH_RATE_LIMIT = "5/minute"
DEFAULT_RATE_LIMIT = "60/minute"

# Module-level limiter instance — imported by routers that need custom limits.
limiter = Limiter(key_func=get_remote_address)


def add_rate_limit_headers(request: Request, response: Response) -> None:
    """Add X-RateLimit-* headers to the response.

    slowapi populates request.state.view_rate_limit when a limit is checked.
    This function reads that state and injects standard headers.
    """
    rate_limit_info = getattr(request.state, "view_rate_limit", None)
    if rate_limit_info:
        # slowapi stores (limit_string, [remaining, reset_at, ...])
        window_stats = rate_limit_info
        # window_stats format: "limit/period remaining reset"
        response.headers["X-RateLimit-Limit"] = str(
            getattr(window_stats, "limit", DEFAULT_RATE_LIMIT)
        )
        response.headers["X-RateLimit-Remaining"] = str(
            getattr(window_stats, "remaining", "")
        )
        response.headers["X-RateLimit-Reset"] = str(
            getattr(window_stats, "reset_at", "")
        )
