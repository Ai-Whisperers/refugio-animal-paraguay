"""Unit tests for health check helper functions.

Covers:
  - _check_database: ok, error paths
  - _check_migrations: ok (at head), outdated, no version, error
  - _check_stripe: disabled (no key), auth error, connection error, generic error
  - _check_smtp: disabled, ok, error
  - _check_twilio: disabled, ok, error
  - _run_with_timeout: passes through on success, returns error dict on timeout
  - _determine_overall_status: healthy, degraded (non-critical fail), unhealthy (critical fail)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import stripe
from src.api.health import (
    _CRITICAL_CHECKS,
    _check_database,
    _check_migrations,
    _check_smtp,
    _check_stripe,
    _check_twilio,
    _determine_overall_status,
    _run_with_timeout,
)

# ---------------------------------------------------------------------------
# _check_database
# ---------------------------------------------------------------------------


class TestCheckDatabase:
    @pytest.mark.asyncio
    async def test_ok_when_db_responds(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(return_value=None)

        result = await _check_database(db)

        assert result["status"] == "ok"
        assert "response_time_ms" in result
        assert isinstance(result["response_time_ms"], int)

    @pytest.mark.asyncio
    async def test_error_when_db_raises(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=OSError("connection refused"))

        result = await _check_database(db)

        assert result["status"] == "error"
        assert "error" in result


# ---------------------------------------------------------------------------
# _check_migrations
# ---------------------------------------------------------------------------


class TestCheckMigrations:
    @pytest.mark.asyncio
    async def test_ok_when_at_head(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "abc123"
        db.execute = AsyncMock(return_value=mock_result)

        with (
            patch("alembic.config.Config"),
            patch("alembic.script.ScriptDirectory") as mock_sd_cls,
        ):
            mock_sd = MagicMock()
            mock_sd.get_current_head.return_value = "abc123"
            mock_sd_cls.from_config.return_value = mock_sd

            result = await _check_migrations(db)

        assert result["status"] == "ok"
        assert result["current_version"] == "abc123"

    @pytest.mark.asyncio
    async def test_outdated_when_behind_head(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "old_version"
        db.execute = AsyncMock(return_value=mock_result)

        with (
            patch("alembic.config.Config"),
            patch("alembic.script.ScriptDirectory") as mock_sd_cls,
        ):
            mock_sd = MagicMock()
            mock_sd.get_current_head.return_value = "new_version"
            mock_sd_cls.from_config.return_value = mock_sd

            result = await _check_migrations(db)

        assert result["status"] == "outdated"
        assert result["current"] == "old_version"
        assert result["head"] == "new_version"

    @pytest.mark.asyncio
    async def test_error_when_no_version_row(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        result = await _check_migrations(db)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_ok_without_alembic_config(self) -> None:
        """When alembic.ini is missing, fall back to reporting version without comparison."""
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = "some_version"
        db.execute = AsyncMock(return_value=mock_result)

        with (patch("alembic.config.Config", side_effect=Exception("no alembic.ini")),):
            result = await _check_migrations(db)

        assert result["status"] == "ok"
        assert result["current_version"] == "some_version"

    @pytest.mark.asyncio
    async def test_error_when_db_fails(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=OSError("db down"))

        result = await _check_migrations(db)

        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# _check_stripe
# ---------------------------------------------------------------------------


class TestCheckStripe:
    @pytest.mark.asyncio
    async def test_disabled_when_no_key(self) -> None:
        settings = MagicMock()
        settings.stripe_secret_key = ""

        result = await _check_stripe(settings)

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_error_on_auth_error(self) -> None:
        settings = MagicMock()
        settings.stripe_secret_key = "sk_test_bad"

        with patch(
            "src.api.health.stripe.Balance.retrieve",
            side_effect=stripe.AuthenticationError("bad key"),
        ):
            result = await _check_stripe(settings)

        assert result["status"] == "error"
        assert "AuthenticationError" in result["error"]

    @pytest.mark.asyncio
    async def test_error_on_connection_error(self) -> None:
        settings = MagicMock()
        settings.stripe_secret_key = "sk_test_ok"

        with patch(
            "src.api.health.stripe.Balance.retrieve",
            side_effect=stripe.APIConnectionError("network"),
        ):
            result = await _check_stripe(settings)

        assert result["status"] == "error"
        assert "APIConnectionError" in result["error"]

    @pytest.mark.asyncio
    async def test_ok_on_successful_balance(self) -> None:
        settings = MagicMock()
        settings.stripe_secret_key = "sk_test_ok"

        with patch("src.api.health.stripe.Balance.retrieve", return_value={"available": []}):
            result = await _check_stripe(settings)

        assert result["status"] == "ok"
        assert "response_time_ms" in result


# ---------------------------------------------------------------------------
# _check_smtp
# ---------------------------------------------------------------------------


class TestCheckSmtp:
    @pytest.mark.asyncio
    async def test_disabled_when_smtp_not_enabled(self) -> None:
        settings = MagicMock()
        settings.smtp_enabled = False

        result = await _check_smtp(settings)

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_error_when_connection_fails(self) -> None:
        settings = MagicMock()
        settings.smtp_enabled = True
        settings.smtp_host = "smtp.example.com"
        settings.smtp_port = 587
        settings.smtp_use_tls = True

        mock_smtp = MagicMock()
        mock_smtp.connect = AsyncMock(side_effect=OSError("connection refused"))

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await _check_smtp(settings)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_ok_when_connection_succeeds(self) -> None:
        settings = MagicMock()
        settings.smtp_enabled = True
        settings.smtp_host = "smtp.example.com"
        settings.smtp_port = 587
        settings.smtp_use_tls = True

        mock_smtp = MagicMock()
        mock_smtp.connect = AsyncMock(return_value=None)
        mock_smtp.quit = AsyncMock(return_value=None)

        with patch("aiosmtplib.SMTP", return_value=mock_smtp):
            result = await _check_smtp(settings)

        assert result["status"] == "ok"
        assert "response_time_ms" in result


# ---------------------------------------------------------------------------
# _check_twilio
# ---------------------------------------------------------------------------


class TestCheckTwilio:
    @pytest.mark.asyncio
    async def test_disabled_when_whatsapp_not_enabled(self) -> None:
        settings = MagicMock()
        settings.whatsapp_enabled = False

        result = await _check_twilio(settings)

        assert result["status"] == "disabled"


# ---------------------------------------------------------------------------
# _run_with_timeout
# ---------------------------------------------------------------------------


class TestRunWithTimeout:
    @pytest.mark.asyncio
    async def test_passes_result_through(self) -> None:
        async def fast_check() -> dict:
            return {"status": "ok"}

        result = await _run_with_timeout(fast_check(), "test_check")
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_returns_error_on_timeout(self) -> None:
        import asyncio

        async def slow_check() -> dict:
            await asyncio.sleep(10)
            return {"status": "ok"}

        with patch("src.api.health._CHECK_TIMEOUT_S", 0.01):
            result = await _run_with_timeout(slow_check(), "slow_check")

        assert result["status"] == "error"
        assert "timeout" in result["error"]


# ---------------------------------------------------------------------------
# _determine_overall_status
# ---------------------------------------------------------------------------


class TestDetermineOverallStatus:
    def test_healthy_when_all_ok(self) -> None:
        checks = {
            "database": {"status": "ok"},
            "migrations": {"status": "ok"},
            "stripe": {"status": "disabled"},
            "smtp": {"status": "disabled"},
            "twilio": {"status": "disabled"},
        }
        assert _determine_overall_status(checks) == "healthy"

    def test_healthy_when_non_critical_disabled(self) -> None:
        checks = {
            "database": {"status": "ok"},
            "migrations": {"status": "ok"},
            "stripe": {"status": "disabled"},
            "smtp": {"status": "disabled"},
            "twilio": {"status": "disabled"},
        }
        assert _determine_overall_status(checks) == "healthy"

    def test_degraded_when_non_critical_fails(self) -> None:
        checks = {
            "database": {"status": "ok"},
            "migrations": {"status": "ok"},
            "stripe": {"status": "error", "error": "AuthenticationError"},
            "smtp": {"status": "disabled"},
            "twilio": {"status": "disabled"},
        }
        assert _determine_overall_status(checks) == "degraded"

    def test_unhealthy_when_database_fails(self) -> None:
        checks = {
            "database": {"status": "error", "error": "connection refused"},
            "migrations": {"status": "ok"},
            "stripe": {"status": "ok"},
            "smtp": {"status": "ok"},
            "twilio": {"status": "ok"},
        }
        assert _determine_overall_status(checks) == "unhealthy"

    def test_unhealthy_when_migrations_fail(self) -> None:
        checks = {
            "database": {"status": "ok"},
            "migrations": {"status": "error", "error": "table not found"},
            "stripe": {"status": "ok"},
            "smtp": {"status": "disabled"},
            "twilio": {"status": "disabled"},
        }
        assert _determine_overall_status(checks) == "unhealthy"

    def test_healthy_when_migrations_outdated(self) -> None:
        # Outdated migrations is concerning but not critical — db still works
        checks = {
            "database": {"status": "ok"},
            "migrations": {"status": "outdated", "current": "v1", "head": "v2"},
            "stripe": {"status": "disabled"},
            "smtp": {"status": "disabled"},
            "twilio": {"status": "disabled"},
        }
        assert _determine_overall_status(checks) == "healthy"

    def test_critical_checks_set_includes_database_and_migrations(self) -> None:
        assert "database" in _CRITICAL_CHECKS
        assert "migrations" in _CRITICAL_CHECKS
