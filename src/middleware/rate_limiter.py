"""Rate limiting configuration using slowapi.

Provides two rate limit tiers:
  - Auth endpoints (/auth/*): 5 requests/minute (brute-force protection)
  - General endpoints: 60 requests/minute (applied as default)

Rate limiting can be disabled via RATE_LIMIT_ENABLED=false in settings,
which is useful for test environments.

The general limit is set as the default_limits on the Limiter, so it applies
to all endpoints automatically. Auth endpoints override with a stricter limit.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Default limit applies to every endpoint unless overridden by a decorator.
GENERAL_RATE_LIMIT = "60/minute"
AUTH_RATE_LIMIT = "5/minute"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[GENERAL_RATE_LIMIT],
    enabled=True,
)


def configure_limiter(*, enabled: bool = True) -> None:
    """Enable or disable the global limiter at runtime.

    Call with enabled=False in test environments to avoid rate-limit interference.
    """
    limiter.enabled = enabled
