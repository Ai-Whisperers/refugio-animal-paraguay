"""Integration tests for one-click email unsubscribe endpoints.

Tests the unsubscribe-link generation and unsubscribe processing endpoints.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_email_unsubscribe.py
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine
from src.services.email_unsubscribe_service import (
    UNSUBSCRIBE_TOKEN_PURPOSE,
)


@pytest_asyncio.fixture(autouse=True)
async def _setup_preferences_table() -> None:
    """Ensure notification_preferences table exists and is clean."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    notification_type VARCHAR(50) NOT NULL,
                    channel VARCHAR(20) NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT true,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_notification_pref_user_type_channel
                        UNIQUE (user_id, notification_type, channel),
                    CONSTRAINT chk_notification_pref_channel
                        CHECK (channel IN ('in_app', 'email')),
                    CONSTRAINT chk_notification_pref_type CHECK (
                        notification_type IN (
                            'adoption_request_created', 'adoption_status_changed',
                            'donation_received', 'donation_refunded',
                            'animal_intake_completed', 'animal_status_changed',
                            'system_alert', 'gdpr_request'
                        )
                    )
                )
            """))
        await session.execute(text("TRUNCATE notification_preferences"))
        await session.commit()


class TestGetUnsubscribeLink:
    """Tests for GET /notification-preferences/unsubscribe-link."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/unsubscribe-link")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_response_has_required_fields(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/unsubscribe-link")
        data = resp.json()
        assert "unsubscribe_url" in data
        assert "expires_in_days" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_expires_in_30_days(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/unsubscribe-link")
        data = resp.json()
        assert data["expires_in_days"] == 30

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_unsubscribe_url_contains_token(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/unsubscribe-link")
        data = resp.json()
        assert "token=" in data["unsubscribe_url"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_token_is_valid_jwt(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/unsubscribe-link")
        data = resp.json()
        url = data["unsubscribe_url"]
        token = url.split("token=", 1)[1]

        settings = Settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["purpose"] == UNSUBSCRIBE_TOKEN_PURPOSE
        assert "sub" in payload

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_requires_authentication(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/notification-preferences/unsubscribe-link")
        assert resp.status_code in (401, 403)


class TestProcessUnsubscribe:
    """Tests for GET /notification-preferences/unsubscribe."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_valid_token_returns_200(self, client: AsyncClient) -> None:
        link_resp = await client.get("/notification-preferences/unsubscribe-link")
        url = link_resp.json()["unsubscribe_url"]
        token = url.split("token=", 1)[1]

        resp = await client.get(f"/notification-preferences/unsubscribe?token={token}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_successful_unsubscribe_returns_message(self, client: AsyncClient) -> None:
        link_resp = await client.get("/notification-preferences/unsubscribe-link")
        url = link_resp.json()["unsubscribe_url"]
        token = url.split("token=", 1)[1]

        resp = await client.get(f"/notification-preferences/unsubscribe?token={token}")
        data = resp.json()
        assert "message" in data
        assert "preferences_updated" in data
        assert data["preferences_updated"] > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_unsubscribe_disables_email_preferences(self, client: AsyncClient) -> None:
        link_resp = await client.get("/notification-preferences/unsubscribe-link")
        url = link_resp.json()["unsubscribe_url"]
        token = url.split("token=", 1)[1]

        await client.get(f"/notification-preferences/unsubscribe?token={token}")

        prefs_resp = await client.get("/notification-preferences")
        prefs_data = prefs_resp.json()
        email_prefs = [p for p in prefs_data["preferences"] if p["channel"] == "email"]
        assert all(p["enabled"] is False for p in email_prefs)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_token_returns_400(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/unsubscribe?token=invalid.garbage.token")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_expired_token_returns_400(self, client: AsyncClient) -> None:
        settings = Settings()
        expired_payload = {
            "sub": "00000000-0000-0000-0000-000000000001",
            "purpose": UNSUBSCRIBE_TOKEN_PURPOSE,
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        }
        expired_token = jwt.encode(
            expired_payload, settings.secret_key, algorithm=settings.algorithm
        )
        resp = await client.get(f"/notification-preferences/unsubscribe?token={expired_token}")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_missing_token_returns_422(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/unsubscribe")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_wrong_purpose_token_returns_400(self, client: AsyncClient) -> None:
        settings = Settings()
        wrong_payload = {
            "sub": "00000000-0000-0000-0000-000000000001",
            "purpose": "login",
            "exp": datetime.now(UTC) + timedelta(days=1),
        }
        wrong_token = jwt.encode(wrong_payload, settings.secret_key, algorithm=settings.algorithm)
        resp = await client.get(f"/notification-preferences/unsubscribe?token={wrong_token}")
        assert resp.status_code == 400
