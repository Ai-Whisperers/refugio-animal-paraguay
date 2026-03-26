"""Unit tests for src/config.py — Settings class."""

import pytest

from src.config import Settings


class TestSettingsDefaults:
    def test_default_database_url_uses_asyncpg_driver(self) -> None:
        s = Settings()
        assert s.database_url.startswith("postgresql+asyncpg://")

    def test_default_database_url_targets_ipv6_loopback(self) -> None:
        # [::1] because Docker container (host-network) owns that interface;
        # host Postgres owns 127.0.0.1:5432 (IPv4).
        s = Settings()
        assert "[::1]" in s.database_url

    def test_default_app_env_is_development(self) -> None:
        s = Settings()
        assert s.app_env == "development"

    def test_default_debug_is_false(self) -> None:
        s = Settings()
        assert s.debug is False

    def test_default_app_name(self) -> None:
        s = Settings()
        assert s.app_name == "Refugio Animal Paraguay"


class TestSettingsEnvOverride:
    def test_database_url_overridden_via_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        url = "postgresql+asyncpg://user:pass@db:5432/mydb"
        monkeypatch.setenv("DATABASE_URL", url)
        s = Settings()
        assert s.database_url == url

    def test_app_env_overridden_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "production")
        s = Settings()
        assert s.app_env == "production"

    def test_debug_overridden_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEBUG", "true")
        s = Settings()
        assert s.debug is True


class TestSettingsValidation:
    def test_invalid_app_env_raises(self) -> None:
        with pytest.raises(ValueError, match="app_env must be one of"):
            Settings(app_env="unknown")

    def test_database_url_without_asyncpg_raises(self) -> None:
        with pytest.raises(ValueError, match="asyncpg driver"):
            Settings(database_url="postgresql://user:pass@localhost/db")

    def test_staging_env_is_valid(self) -> None:
        s = Settings(app_env="staging")
        assert s.app_env == "staging"


class TestSettingsProperties:
    def test_is_production_false_in_development(self) -> None:
        s = Settings(app_env="development")
        assert s.is_production is False

    def test_is_production_true_in_production(self) -> None:
        s = Settings(app_env="production")
        assert s.is_production is True
