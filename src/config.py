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

    # Tigo Money (local PYG payments)
    tigo_money_enabled: bool = Field(
        default=False,
        description="Enable Tigo Money payment option. Requires tigo_merchant_id and tigo_api_key.",
    )
    tigo_merchant_id: str = Field(
        default="",
        description="Tigo Money merchant account identifier.",
    )
    tigo_api_key: str = Field(
        default="",
        description="Tigo Money API key for authenticating payment requests.",
    )
    tigo_webhook_secret: str = Field(
        default="",
        description="Secret used to verify Tigo Money webhook callback signatures.",
    )
    tigo_api_base_url: str = Field(
        default="https://api.tigo.com.py/v1",
        description="Tigo Money API base URL. Override for sandbox/staging environments.",
    )

    # Google OAuth
    google_client_id: str = Field(
        default="",
        description="Google OAuth2 client ID. Required for social login.",
    )
    google_client_secret: str = Field(
        default="",
        description="Google OAuth2 client secret. Required for social login.",
    )
    google_redirect_uri: str = Field(
        default="http://localhost:3000/auth/google/callback",
        description="OAuth2 redirect URI. Must match Google Cloud Console configuration.",
    )
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend base URL for redirects after OAuth.",
    )

    # Sentry error tracking
    sentry_dsn: str = Field(
        default="",
        description=(
            "Sentry DSN for error tracking. Leave empty to disable Sentry. "
            "Required in production: https://sentry.io"
        ),
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description=(
            "Fraction of transactions to send to Sentry for performance monitoring "
            "(0.0 = none, 1.0 = all). Keep low in production to control costs."
        ),
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

    # WhatsApp / Twilio
    whatsapp_enabled: bool = Field(
        default=False,
        description="Enable WhatsApp message delivery via Twilio. Disable in tests and local dev.",
    )
    twilio_account_sid: str = Field(
        default="",
        description="Twilio Account SID. Required when whatsapp_enabled=True.",
    )
    twilio_auth_token: str = Field(
        default="",
        description="Twilio Auth Token. Required when whatsapp_enabled=True.",
    )
    twilio_whatsapp_from: str = Field(
        default="whatsapp:+14155238886",
        description=(
            "Twilio WhatsApp sender number in E.164 format with 'whatsapp:' prefix. "
            "Use the Twilio sandbox number for development."
        ),
    )

    # Donor tax ID encryption
    donor_tax_id_encryption_key: str = Field(
        default="",
        description=(
            "Fernet encryption key for donor BSN/TIN storage. "
            "Generate with: python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'. "
            "Required in production when storing donor tax IDs."
        ),
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
