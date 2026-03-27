"""Sentry error tracking configuration.

Sentry is initialised at application startup when a DSN is configured.
If ``sentry_dsn`` is empty (default for development), Sentry is disabled
and the function returns silently — no network calls, no side effects.

Usage::

    from src.sentry_config import configure_sentry
    configure_sentry(dsn=settings.sentry_dsn, environment=settings.app_env,
                     traces_sample_rate=settings.sentry_traces_sample_rate)
"""

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# SDK version exposed for testing / health endpoints
SENTRY_SDK_VERSION = sentry_sdk.VERSION

_ENABLED_FLAG: bool = False


def configure_sentry(
    *,
    dsn: str,
    environment: str,
    traces_sample_rate: float = 0.1,
    release: str | None = None,
) -> bool:
    """Initialise Sentry with FastAPI and SQLAlchemy integrations.

    Args:
        dsn: Sentry project DSN.  Pass an empty string to disable.
        environment: Deployment environment label (e.g. ``"production"``).
        traces_sample_rate: 0.0-1.0 fraction of transactions to sample.
        release: Optional release string (e.g. a git SHA or semver tag).

    Returns:
        ``True`` if Sentry was initialised, ``False`` if disabled (no DSN).
    """
    global _ENABLED_FLAG

    dsn = dsn.strip()
    if not dsn:
        _ENABLED_FLAG = False
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=traces_sample_rate,
        release=release,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        # Do not send PII (IP addresses, user emails) to Sentry by default.
        send_default_pii=False,
    )
    _ENABLED_FLAG = True
    return True


def is_sentry_enabled() -> bool:
    """Return whether Sentry was successfully initialised in this process."""
    return _ENABLED_FLAG


__all__ = [
    "SENTRY_SDK_VERSION",
    "configure_sentry",
    "is_sentry_enabled",
]
