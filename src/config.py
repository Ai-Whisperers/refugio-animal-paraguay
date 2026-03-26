"""Application settings loaded from environment variables.

Pydantic-settings reads values from environment variables (case-insensitive).
All settings have sensible defaults for local development; production deployments
must supply DATABASE_URL and set APP_ENV=production.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Refugio Animal Paraguay application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        # IPv6 [::1] used because the Docker container (host-network mode) owns that
        # interface while the host Postgres owns 127.0.0.1:5432 (IPv4).
        default="postgresql+asyncpg://refugio_user:refugio_pass@[::1]:5432/refugio_dev",
        description="Async SQLAlchemy database URL. Must use asyncpg driver for async FastAPI.",
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        # asyncpg driver required for async SQLAlchemy; psycopg2 is sync-only.
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "database_url must use the asyncpg driver: postgresql+asyncpg://..."
            )
        return value

    # Application
    app_env: str = Field(
        default="development",
        description="Runtime environment: development | staging | production",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode. Must be False in production.",
    )
    app_name: str = Field(
        default="Refugio Animal Paraguay",
        description="Human-readable application name, used in API metadata.",
    )

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        allowed = {"development", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got: {value!r}")
        return value

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.app_env == "production"


def get_settings() -> Settings:
    """Return application settings instance.

    Intended for use as a FastAPI dependency:
        settings = Depends(get_settings)
    """
    return Settings()
