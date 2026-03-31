"""Integration tests for notification frequency API endpoints.

Tests the frequency GET/PUT endpoints with a live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_notification_frequency.py
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine


@pytest_asyncio.fixture(autouse=True)
async def _setup_frequency_table() -> None:
    """Create notification_channel_frequency table if it doesn't exist."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
                CREATE TABLE IF NOT EXISTS notification_channel_frequency (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    channel VARCHAR(20) NOT NULL,
                    frequency VARCHAR(20) NOT NULL DEFAULT 'immediate',
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_notification_channel_frequency_user_channel
                        UNIQUE (user_id, channel),
                    CONSTRAINT chk_notification_channel_frequency_channel
                        CHECK (channel IN ('in_app', 'email')),
                    CONSTRAINT chk_notification_channel_frequency_value
                        CHECK (frequency IN ('immediate', 'daily_digest', 'weekly'))
                )
            """))
        await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_notification_channel_frequency_user
                ON notification_channel_frequency (user_id)
            """))
        await session.execute(text("TRUNCATE notification_channel_frequency"))
        await session.commit()


class TestGetFrequency:
    """Tests for GET /notification-preferences/frequency."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/frequency")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_returns_all_channels(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/frequency")
        data = resp.json()
        assert "frequencies" in data
        channels = {f["channel"] for f in data["frequencies"]}
        assert channels == {"in_app", "email"}

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_defaults_are_immediate(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/frequency")
        data = resp.json()
        for entry in data["frequencies"]:
            assert entry["frequency"] == "immediate"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_response_has_required_fields(self, client: AsyncClient) -> None:
        resp = await client.get("/notification-preferences/frequency")
        data = resp.json()
        for entry in data["frequencies"]:
            assert "channel" in entry
            assert "frequency" in entry


class TestUpdateFrequency:
    """Tests for PUT /notification-preferences/frequency."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_returns_200(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences/frequency",
            json={
                "frequencies": [
                    {"channel": "email", "frequency": "daily_digest"},
                ]
            },
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_persists_frequency(self, client: AsyncClient) -> None:
        await client.put(
            "/notification-preferences/frequency",
            json={
                "frequencies": [
                    {"channel": "email", "frequency": "weekly"},
                ]
            },
        )

        resp = await client.get("/notification-preferences/frequency")
        data = resp.json()
        email_entry = next(f for f in data["frequencies"] if f["channel"] == "email")
        assert email_entry["frequency"] == "weekly"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_returns_full_frequency_list(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences/frequency",
            json={
                "frequencies": [
                    {"channel": "email", "frequency": "daily_digest"},
                ]
            },
        )
        data = resp.json()
        assert "frequencies" in data
        channels = {f["channel"] for f in data["frequencies"]}
        assert channels == {"in_app", "email"}

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_rejects_invalid_frequency(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences/frequency",
            json={
                "frequencies": [
                    {"channel": "email", "frequency": "hourly"},
                ]
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_rejects_invalid_channel(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences/frequency",
            json={
                "frequencies": [
                    {"channel": "sms", "frequency": "immediate"},
                ]
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_rejects_empty_list(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/notification-preferences/frequency",
            json={"frequencies": []},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_idempotent_update(self, client: AsyncClient) -> None:
        payload = {
            "frequencies": [
                {"channel": "email", "frequency": "daily_digest"},
            ]
        }
        await client.put("/notification-preferences/frequency", json=payload)
        resp = await client.put("/notification-preferences/frequency", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        email_entry = next(f for f in data["frequencies"] if f["channel"] == "email")
        assert email_entry["frequency"] == "daily_digest"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_all_frequency_values_accepted(self, client: AsyncClient) -> None:
        for freq in ["immediate", "daily_digest", "weekly"]:
            resp = await client.put(
                "/notification-preferences/frequency",
                json={"frequencies": [{"channel": "email", "frequency": freq}]},
            )
            assert resp.status_code == 200
