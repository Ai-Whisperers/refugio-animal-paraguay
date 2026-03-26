"""Integration tests for notification preferences API endpoints.

Tests the preference CRUD endpoints with a live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_notification_preferences.py
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine


@pytest_asyncio.fixture(autouse=True)
async def _setup_preferences_table() -> None:
    """Create notification_preferences table if it doesn't exist."""
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
        await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_notification_pref_user
                ON notification_preferences (user_id)
            """))
        await session.execute(text("TRUNCATE notification_preferences"))
        await session.commit()


class TestListPreferences:
    """Tests for GET /notification-preferences."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert "preferences" in data
        # Should return full matrix (8 types x 2 channels = 16)
        assert len(data["preferences"]) == 16

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_defaults_are_enabled(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences")
        assert resp.status_code == 200
        data = resp.json()
        for pref in data["preferences"]:
            assert pref["enabled"] is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_preferences_have_required_fields(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences")
        data = resp.json()
        for pref in data["preferences"]:
            assert "notification_type" in pref
            assert "channel" in pref
            assert "enabled" in pref


class TestUpdatePreferences:
    """Tests for PUT /notification-preferences."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_returns_200(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences",
            json={
                "preferences": [
                    {
                        "notification_type": "donation_received",
                        "channel": "email",
                        "enabled": False,
                    }
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "preferences" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_persists_disabled_preference(self, client: AsyncClient) -> None:
        # Disable a preference
        await client.put(
            "/notification-preferences",
            json={
                "preferences": [
                    {
                        "notification_type": "system_alert",
                        "channel": "in_app",
                        "enabled": False,
                    }
                ]
            },
        )

        # Read back
        resp = await client.get("/notification-preferences")
        data = resp.json()
        matching = [
            p
            for p in data["preferences"]
            if p["notification_type"] == "system_alert" and p["channel"] == "in_app"
        ]
        assert len(matching) == 1
        assert matching[0]["enabled"] is False

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_rejects_invalid_type(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences",
            json={
                "preferences": [
                    {
                        "notification_type": "invalid_type",
                        "channel": "email",
                        "enabled": False,
                    }
                ]
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_rejects_invalid_channel(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences",
            json={
                "preferences": [
                    {
                        "notification_type": "donation_received",
                        "channel": "sms",
                        "enabled": False,
                    }
                ]
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_rejects_empty_list(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences",
            json={"preferences": []},
        )
        assert resp.status_code == 422
