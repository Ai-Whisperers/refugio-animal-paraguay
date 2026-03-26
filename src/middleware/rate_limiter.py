"""Rate limiting configuration using slowapi.

Provides a global limiter instance and helper for applying rate limits
to individual routes. Uses in-memory storage (sufficient for single-instance MVP).

Default rate limits:
  - Auth endpoints: 5/minute (applied via @limiter.limit decorator)
  - General endpoints: 60/minute (set as default_limits)

Rate limiting is controlled by the RATE_LIMIT_ENABLED setting. When disabled,
the limiter is created with enabled=False (no limits enforced).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import get_settings

_settings = get_settings()

# Global limiter instance — imported by route modules to apply per-route limits.
# default_limits applies 60/minute to all routes unless overridden per-route.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    enabled=_settings.rate_limit_enabled,
)
