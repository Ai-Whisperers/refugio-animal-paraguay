"""Unit tests for Sentry error tracking configuration.

Tests cover:
- configure_sentry returns False and skips init when DSN is empty
- configure_sentry returns True and calls sentry_sdk.init when DSN is set
- is_sentry_enabled reflects the last configure_sentry call
- sentry_sdk.init receives correct keyword arguments
- No-op path leaves Sentry un-initialised (no side effects)
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from src.sentry_config import configure_sentry, is_sentry_enabled


class TestConfigureSentryDisabled:
    """When DSN is empty Sentry must not be initialised."""

    def test_returns_false_when_dsn_is_empty(self) -> None:
        result = configure_sentry(dsn="", environment="production")
        assert result is False

    def test_returns_false_when_dsn_is_whitespace(self) -> None:
        result = configure_sentry(dsn="   ", environment="production")
        # Whitespace-only DSN is treated as empty (falsy)
        assert result is False

    def test_sentry_init_not_called_when_dsn_is_empty(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn="", environment="development")
        mock_init.assert_not_called()

    def test_is_sentry_enabled_false_after_empty_dsn(self) -> None:
        configure_sentry(dsn="", environment="development")
        assert is_sentry_enabled() is False


class TestConfigureSentryEnabled:
    """When a valid DSN is provided Sentry must be initialised correctly."""

    _FAKE_DSN = "https://abc123@o000.ingest.sentry.io/0"

    def test_returns_true_when_dsn_is_set(self) -> None:
        with patch("sentry_sdk.init"):
            result = configure_sentry(dsn=self._FAKE_DSN, environment="production")
        assert result is True

    def test_sentry_init_called_once(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn=self._FAKE_DSN, environment="staging")
        mock_init.assert_called_once()

    def test_sentry_init_receives_dsn(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn=self._FAKE_DSN, environment="production")
        _, kwargs = mock_init.call_args
        assert kwargs["dsn"] == self._FAKE_DSN

    def test_sentry_init_receives_environment(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn=self._FAKE_DSN, environment="staging")
        _, kwargs = mock_init.call_args
        assert kwargs["environment"] == "staging"

    def test_sentry_init_receives_traces_sample_rate(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn=self._FAKE_DSN, environment="production", traces_sample_rate=0.5)
        _, kwargs = mock_init.call_args
        assert kwargs["traces_sample_rate"] == pytest.approx(0.5)

    def test_default_traces_sample_rate_is_01(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn=self._FAKE_DSN, environment="production")
        _, kwargs = mock_init.call_args
        assert kwargs["traces_sample_rate"] == pytest.approx(0.1)

    def test_send_default_pii_is_false(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn=self._FAKE_DSN, environment="production")
        _, kwargs = mock_init.call_args
        assert kwargs["send_default_pii"] is False

    def test_is_sentry_enabled_true_after_valid_dsn(self) -> None:
        with patch("sentry_sdk.init"):
            configure_sentry(dsn=self._FAKE_DSN, environment="production")
        assert is_sentry_enabled() is True

    def test_release_passed_through_when_set(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(
                dsn=self._FAKE_DSN,
                environment="production",
                release="1.2.3",
            )
        _, kwargs = mock_init.call_args
        assert kwargs["release"] == "1.2.3"

    def test_release_defaults_to_none(self) -> None:
        with patch("sentry_sdk.init") as mock_init:
            configure_sentry(dsn=self._FAKE_DSN, environment="production")
        _, kwargs = mock_init.call_args
        assert kwargs.get("release") is None


class TestIsSentryEnabled:
    """is_sentry_enabled reflects last configure_sentry call."""

    _FAKE_DSN = "https://abc123@o000.ingest.sentry.io/0"

    def test_disabled_after_empty_dsn_call(self) -> None:
        configure_sentry(dsn="", environment="development")
        assert is_sentry_enabled() is False

    def test_enabled_after_valid_dsn_call(self) -> None:
        with patch("sentry_sdk.init"):
            configure_sentry(dsn=self._FAKE_DSN, environment="production")
        assert is_sentry_enabled() is True

    def test_can_be_toggled_off(self) -> None:
        with patch("sentry_sdk.init"):
            configure_sentry(dsn=self._FAKE_DSN, environment="production")
        assert is_sentry_enabled() is True
        configure_sentry(dsn="", environment="production")
        assert is_sentry_enabled() is False
