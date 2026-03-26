"""Unit tests for in-app notification service logic.

Tests notification CRUD operations, pagination, read status management,
and deletion with mocked database sessions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.notification import NotificationType
from src.services.notification_service import (
    create_notification,
    delete_notification,
    get_unread_count,
    list_notifications,
    mark_all_read,
    mark_read,
)


class TestCreateNotification:
    """Tests for create_notification function."""

    @pytest.mark.asyncio
    async def test_creates_notification_with_all_fields(self) -> None:
        db = AsyncMock()
        user_id = uuid4()

        result = await create_notification(
            db,
            user_id=user_id,
            notification_type=NotificationType.DONATION_RECEIVED,
            title="Donation Received",
            message="Jan donated 50 EUR.",
            data={"amount": "50", "currency": "EUR"},
        )

        assert result is not None
        assert result.user_id == user_id
        assert result.notification_type == NotificationType.DONATION_RECEIVED
        assert result.title == "Donation Received"
        assert result.message == "Jan donated 50 EUR."
        assert result.data == {"amount": "50", "currency": "EUR"}
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_creates_notification_without_data(self) -> None:
        db = AsyncMock()

        result = await create_notification(
            db,
            user_id=uuid4(),
            notification_type=NotificationType.SYSTEM_ALERT,
            title="System Alert",
            message="Scheduled maintenance tonight.",
        )

        assert result.data is None

    @pytest.mark.asyncio
    async def test_creates_notification_with_each_type(self) -> None:
        db = AsyncMock()
        for ntype in NotificationType:
            result = await create_notification(
                db,
                user_id=uuid4(),
                notification_type=ntype,
                title=f"Test {ntype}",
                message=f"Testing {ntype} notification.",
            )
            assert result.notification_type == ntype


class TestListNotifications:
    """Tests for list_notifications function."""

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        n1, n2 = MagicMock(), MagicMock()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [n1, n2]
        db.execute.return_value = mock_result

        result = await list_notifications(db, uuid4())
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await list_notifications(db, uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_filters_by_read_status(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        await list_notifications(db, uuid4(), is_read=False)
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_caps_limit_at_max_page_size(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        # Request limit > MAX_PAGE_SIZE (100)
        await list_notifications(db, uuid4(), limit=500)
        db.execute.assert_awaited_once()


class TestGetUnreadCount:
    """Tests for get_unread_count function."""

    @pytest.mark.asyncio
    async def test_returns_count(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        db.execute.return_value = mock_result

        count = await get_unread_count(db, uuid4())
        assert count == 5

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_unread(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        db.execute.return_value = mock_result

        count = await get_unread_count(db, uuid4())
        assert count == 0


class TestMarkRead:
    """Tests for mark_read function."""

    @pytest.mark.asyncio
    async def test_marks_unread_notification_as_read(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        notification = MagicMock()
        notification.user_id = user_id
        notification.is_read = False
        notification.read_at = None
        db.get.return_value = notification

        result = await mark_read(db, uuid4(), user_id)

        assert result is not None
        assert result.is_read is True
        assert result.read_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_already_read_notification_without_update(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        notification = MagicMock()
        notification.user_id = user_id
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        db.get.return_value = notification

        result = await mark_read(db, uuid4(), user_id)

        assert result is not None
        # flush should not be called since it's already read
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await mark_read(db, uuid4(), uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_wrong_user(self) -> None:
        db = AsyncMock()
        notification = MagicMock()
        notification.user_id = uuid4()  # Different user
        db.get.return_value = notification

        result = await mark_read(db, uuid4(), uuid4())
        assert result is None


class TestMarkAllRead:
    """Tests for mark_all_read function."""

    @pytest.mark.asyncio
    async def test_marks_all_unread_as_read(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 3
        db.execute.return_value = mock_result

        count = await mark_all_read(db, uuid4())

        assert count == 3
        db.execute.assert_awaited_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_zero_when_none_unread(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        db.execute.return_value = mock_result

        count = await mark_all_read(db, uuid4())
        assert count == 0


class TestDeleteNotification:
    """Tests for delete_notification function."""

    @pytest.mark.asyncio
    async def test_deletes_own_notification(self) -> None:
        db = AsyncMock()
        user_id = uuid4()
        notification = MagicMock()
        notification.user_id = user_id
        db.get.return_value = notification

        result = await delete_notification(db, uuid4(), user_id)

        assert result is True
        db.delete.assert_awaited_once_with(notification)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await delete_notification(db, uuid4(), uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_wrong_user(self) -> None:
        db = AsyncMock()
        notification = MagicMock()
        notification.user_id = uuid4()
        db.get.return_value = notification

        result = await delete_notification(db, uuid4(), uuid4())
        assert result is False
        db.delete.assert_not_awaited()
