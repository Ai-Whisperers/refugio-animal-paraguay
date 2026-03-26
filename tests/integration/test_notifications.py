"""Integration tests for in-app notifications API endpoints.

Tests the notification CRUD endpoints with a live database.

Requires a live PostgreSQL instance (refugio_dev).
Run: pytest -m integration tests/integration/test_notifications.py
"""

from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine


@pytest_asyncio.fixture(autouse=True)
async def _setup_notifications_table() -> None:
    """Create notifications table if it doesn't exist."""
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id),
                    notification_type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    data JSONB,
                    is_read BOOLEAN NOT NULL DEFAULT false,
                    read_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT chk_notification_type CHECK (
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
                CREATE INDEX IF NOT EXISTS ix_notifications_user_id
                ON notifications (user_id)
            """))
        await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_notifications_user_read
                ON notifications (user_id, is_read)
            """))
        await session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_notifications_user_created
                ON notifications (user_id, created_at)
            """))
        await session.commit()


class TestListNotifications:
    """Tests for GET /notifications."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/notifications")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_with_read_filter(self, client: AsyncClient) -> None:
        resp = await client.get("/notifications?is_read=false")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_with_pagination(self, client: AsyncClient) -> None:
        resp = await client.get("/notifications?offset=0&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 10


class TestUnreadCount:
    """Tests for GET /notifications/unread-count."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_unread_count_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/notifications/unread-count")
        assert resp.status_code == 200
        data = resp.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)


class TestCreateNotification:
    """Tests for POST /notifications (admin only)."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_returns_403_for_staff(self, client: AsyncClient) -> None:
        """Staff user should not be able to create notifications (admin only)."""
        resp = await client.post(
            "/notifications",
            json={
                "user_id": str(uuid4()),
                "notification_type": "system_alert",
                "title": "Test Alert",
                "message": "This is a test.",
            },
        )
        # Default test client is staff, not admin — should get 403
        assert resp.status_code == 403

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_rejects_invalid_type_with_403(self, client: AsyncClient) -> None:
        """Staff cannot create notifications — 403 takes precedence over validation."""
        resp = await client.post(
            "/notifications",
            json={
                "user_id": str(uuid4()),
                "notification_type": "invalid_type",
                "title": "Bad Type",
                "message": "Should fail.",
            },
        )
        # Admin-only endpoint returns 403 for staff before body validation
        assert resp.status_code == 403


class TestMarkRead:
    """Tests for PATCH /notifications/{id}/read."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mark_read_returns_404_for_missing(self, client: AsyncClient) -> None:
        resp = await client.patch(f"/notifications/{uuid4()}/read")
        assert resp.status_code == 404


class TestDeleteNotification:
    """Tests for DELETE /notifications/{id}."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_returns_404_for_missing(self, client: AsyncClient) -> None:
        resp = await client.delete(f"/notifications/{uuid4()}")
        assert resp.status_code == 404


class TestMarkAllRead:
    """Tests for POST /notifications/mark-all-read."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_mark_all_read_returns_200(self, client: AsyncClient) -> None:
        resp = await client.post("/notifications/mark-all-read")
        assert resp.status_code == 200
        data = resp.json()
        assert "marked_count" in data
