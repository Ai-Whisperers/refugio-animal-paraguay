"""Health check endpoint.

Returns application status and dependency health for all critical services.
Used by load balancers, monitoring systems, and alerting pipelines.

Endpoints:
  GET /health  — returns overall status + per-dependency checks with response times
"""

import asyncio
import logging
import time
from datetime import UTC, datetime

import stripe
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings, get_settings
from src.db.session import get_db
from src.schemas.error import COMMON_RESPONSES

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"], responses=COMMON_RESPONSES)

_DB_PING_QUERY = text("SELECT 1")
_MIGRATION_VERSION_QUERY = text("SELECT version_num FROM alembic_version")

# Checks that cause "unhealthy" status (DB and migrations are critical)
_CRITICAL_CHECKS = frozenset({"database", "migrations"})

# Individual check timeout in seconds
_CHECK_TIMEOUT_S = 2.0


async def _check_database(db: AsyncSession) -> dict:
    """Verify database connectivity with a simple SELECT 1 ping."""
    start = time.monotonic()
    try:
        await db.execute(_DB_PING_QUERY)
        return {
            "status": "ok",
            "response_time_ms": int((time.monotonic() - start) * 1000),
        }
    except Exception as exc:
        logger.error("health_check: database unreachable: %s", type(exc).__name__)
        return {
            "status": "error",
            "error": type(exc).__name__,
        }


async def _check_migrations(db: AsyncSession) -> dict:
    """Verify the database is at the expected Alembic migration head."""
    try:
        result = await db.execute(_MIGRATION_VERSION_QUERY)
        current_version: str | None = result.scalar()
        if current_version is None:
            return {"status": "error", "error": "No migration version found in alembic_version"}

        # Compare with the head known to Alembic's script directory
        try:
            from alembic.config import Config
            from alembic.script import ScriptDirectory

            cfg = Config("alembic.ini")
            script = ScriptDirectory.from_config(cfg)
            head = script.get_current_head()

            if current_version == head:
                return {"status": "ok", "current_version": current_version}
            return {
                "status": "outdated",
                "current": current_version,
                "head": head,
            }
        except Exception:
            # If Alembic config is unavailable (containers without alembic.ini),
            # report version without comparison
            return {"status": "ok", "current_version": current_version}

    except Exception as exc:
        logger.error("health_check: migrations check failed: %s", type(exc).__name__)
        return {"status": "error", "error": type(exc).__name__}


async def _check_stripe(settings: Settings) -> dict:
    """Verify Stripe API connectivity with a read-only balance retrieval."""
    key = settings.stripe_secret_key
    if not key:
        return {"status": "disabled"}

    start = time.monotonic()
    try:
        stripe.api_key = key
        # Balance retrieval is a safe, read-only operation
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: stripe.Balance.retrieve())
        return {
            "status": "ok",
            "response_time_ms": int((time.monotonic() - start) * 1000),
        }
    except stripe.AuthenticationError:
        logger.error("health_check: stripe authentication failed")
        return {"status": "error", "error": "AuthenticationError"}
    except stripe.APIConnectionError:
        logger.error("health_check: stripe API unreachable")
        return {"status": "error", "error": "APIConnectionError"}
    except Exception as exc:
        logger.warning("health_check: stripe check failed: %s", type(exc).__name__)
        return {"status": "error", "error": type(exc).__name__}


async def _check_smtp(settings: Settings) -> dict:
    """Verify SMTP connectivity by opening and closing a connection."""
    if not settings.smtp_enabled:
        return {"status": "disabled"}

    start = time.monotonic()
    try:
        import aiosmtplib

        smtp = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            use_tls=settings.smtp_use_tls,
            timeout=_CHECK_TIMEOUT_S,
        )
        await smtp.connect()
        await smtp.quit()
        return {
            "status": "ok",
            "response_time_ms": int((time.monotonic() - start) * 1000),
        }
    except Exception as exc:
        logger.warning("health_check: smtp check failed: %s", type(exc).__name__)
        return {"status": "error", "error": type(exc).__name__}


async def _check_twilio(settings: Settings) -> dict:
    """Verify Twilio API connectivity by fetching account info."""
    if not settings.whatsapp_enabled:
        return {"status": "disabled"}

    start = time.monotonic()
    try:
        from twilio.rest import Client

        loop = asyncio.get_event_loop()
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        await loop.run_in_executor(
            None,
            lambda: client.api.accounts(settings.twilio_account_sid).fetch(),
        )
        return {
            "status": "ok",
            "response_time_ms": int((time.monotonic() - start) * 1000),
        }
    except Exception as exc:
        logger.warning("health_check: twilio check failed: %s", type(exc).__name__)
        return {"status": "error", "error": type(exc).__name__}


async def _run_with_timeout(coro: object, check_name: str) -> dict:
    """Run a check coroutine with a timeout guard.

    Returns a timeout error dict if the check exceeds _CHECK_TIMEOUT_S.
    """
    try:
        return await asyncio.wait_for(coro, timeout=_CHECK_TIMEOUT_S)  # type: ignore[arg-type]
    except TimeoutError:
        logger.warning("health_check: %s timed out after %.1fs", check_name, _CHECK_TIMEOUT_S)
        return {"status": "error", "error": f"timeout after {_CHECK_TIMEOUT_S:.0f}s"}


def _determine_overall_status(checks: dict[str, dict]) -> str:
    """Derive overall health status from individual check results.

    Rules:
      - "unhealthy"  if any critical check (database / migrations) reports error
      - "degraded"   if any non-critical check reports error
      - "healthy"    otherwise (includes "disabled" and "outdated" statuses)
    """
    for name in _CRITICAL_CHECKS:
        check = checks.get(name, {})
        if check.get("status") not in ("ok", "outdated", "disabled"):
            return "unhealthy"

    for name, check in checks.items():
        if name not in _CRITICAL_CHECKS and check.get("status") == "error":
            return "degraded"

    return "healthy"


@router.get("/health")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Comprehensive health check for all critical dependencies.

    Runs database, migration, Stripe, SMTP, and Twilio checks concurrently.
    Each check has a 2-second timeout so the endpoint completes within ~5 seconds.

    Returns:
        200 with status "healthy" or "degraded" when the service can handle traffic.
        503 with status "unhealthy" when critical dependencies (DB / migrations) fail.
    """
    db_result, migrations_result, stripe_result, smtp_result, twilio_result = await asyncio.gather(
        _run_with_timeout(_check_database(db), "database"),
        _run_with_timeout(_check_migrations(db), "migrations"),
        _run_with_timeout(_check_stripe(settings), "stripe"),
        _run_with_timeout(_check_smtp(settings), "smtp"),
        _run_with_timeout(_check_twilio(settings), "twilio"),
    )

    checks: dict[str, dict] = {
        "database": db_result,
        "migrations": migrations_result,
        "stripe": stripe_result,
        "smtp": smtp_result,
        "twilio": twilio_result,
    }

    overall_status = _determine_overall_status(checks)

    logger.info(
        "health_check_completed",
        extra={
            "overall_status": overall_status,
            "database_status": db_result.get("status"),
            "migrations_status": migrations_result.get("status"),
        },
    )

    if overall_status == "unhealthy":
        response.status_code = 503

    return {
        "status": overall_status,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks": checks,
    }
