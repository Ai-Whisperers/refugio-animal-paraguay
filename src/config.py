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
            raise ValueError("database_url must use the asyncpg driver: postgresql+asyncpg://...")
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

    # Auth
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-must-be-32-chars-min",
        description="JWT signing secret. Must be ≥32 chars in production.",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm.",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token lifetime in minutes.",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        return value

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000",
        description=(
            "Comma-separated list of allowed CORS origins. "
            "Use '*' for development only — never in production."
        ),
    )

    # Email / SMTP
    smtp_enabled: bool = Field(
        default=False,
        description="Enable email sending. Disable in tests and local dev.",
    )
    smtp_host: str = Field(
        default="localhost",
        description="SMTP server hostname.",
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port (587 for STARTTLS, 465 for TLS).",
    )
    smtp_username: str = Field(
        default="",
        description="SMTP authentication username.",
    )
    smtp_password: str = Field(
        default="",
        description="SMTP authentication password.",
    )
    smtp_use_tls: bool = Field(
        default=True,
        description="Use TLS for SMTP connection.",
    )
    email_from_address: str = Field(
        default="noreply@refugioanimal.org",
        description="Default sender email address.",
    )
    email_from_name: str = Field(
        default="Refugio Animal Paraguay",
        description="Default sender display name.",
    )

    # Stripe
    stripe_secret_key: str = Field(
        default="",
        description="Stripe API secret key. Required for payment processing.",
    )
    stripe_webhook_secret: str = Field(
        default="",
        description="Stripe webhook signing secret (whsec_...). Required to verify webhook signatures.",
    )

    # Rate limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable/disable rate limiting globally. Disable in test environments.",
    )
    rate_limit_auth: str = Field(
        default="5/minute",
        description="Rate limit for auth endpoints (slowapi format).",
    )
    rate_limit_general: str = Field(
        default="60/minute",
        description="Rate limit for general API endpoints (slowapi format).",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list of origin strings."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

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
