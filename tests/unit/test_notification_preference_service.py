"""Unit tests for notification preference service logic.

Tests preference CRUD, default filling, and preference checking
with mocked database sessions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.notification_preference_service import (
    CHANNELS,
    NOTIFICATION_TYPES,
    get_preferences,
    get_preferences_with_defaults,
    is_notification_enabled,
    update_preferences,
)


class TestGetPreferences:
    """Tests for get_preferences function."""

    @pytest.mark.asyncio
    async def test_returns_existing_preferences(self) -> None:
        p1, p2 = MagicMock(), MagicMock()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [p1, p2]
        db.execute.return_value = mock_result

        result = await get_preferences(db, uuid4())
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_for_new_user(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_preferences(db, uuid4())
        assert result == []


class TestGetPreferencesWithDefaults:
    """Tests for get_preferences_with_defaults function."""

    @pytest.mark.asyncio
    async def test_returns_full_matrix_for_new_user(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_preferences_with_defaults(db, uuid4())

        expected_count = len(NOTIFICATION_TYPES) * len(CHANNELS)
        assert len(result) == expected_count
        # All defaults should be enabled
        assert all(p["enabled"] is True for p in result)

    @pytest.mark.asyncio
    async def test_respects_disabled_preference(self) -> None:
        db = AsyncMock()
        # One disabled preference
        pref = MagicMock()
        pref.notification_type = "donation_received"
        pref.channel = "email"
        pref.enabled = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pref]
        db.execute.return_value = mock_result

        result = await get_preferences_with_defaults(db, uuid4())

        # Find the donation_received+email entry
        matching = [
            p
            for p in result
            if p["notification_type"] == "donation_received" and p["channel"] == "email"
        ]
        assert len(matching) == 1
        assert matching[0]["enabled"] is False

    @pytest.mark.asyncio
    async def test_other_preferences_remain_enabled(self) -> None:
        db = AsyncMock()
        pref = MagicMock()
        pref.notification_type = "system_alert"
        pref.channel = "in_app"
        pref.enabled = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [pref]
        db.execute.return_value = mock_result

        result = await get_preferences_with_defaults(db, uuid4())

        # All except the one disabled should be True
        disabled = [p for p in result if p["enabled"] is False]
        assert len(disabled) == 1
        assert disabled[0]["notification_type"] == "system_alert"
        assert disabled[0]["channel"] == "in_app"


class TestUpdatePreferences:
    """Tests for update_preferences function."""

    @pytest.mark.asyncio
    async def test_creates_new_preference(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        updates = [
            {
                "notification_type": "donation_received",
                "channel": "email",
                "enabled": False,
            }
        ]

        result = await update_preferences(db, uuid4(), updates)

        assert len(result) == 1
        db.add.assert_called_once()
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_updates_existing_preference(self) -> None:
        db = AsyncMock()
        existing = MagicMock()
        existing.enabled = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        updates = [
            {
                "notification_type": "system_alert",
                "channel": "in_app",
                "enabled": False,
            }
        ]

        result = await update_preferences(db, uuid4(), updates)

        assert len(result) == 1
        assert existing.enabled is False
        db.add.assert_not_called()  # Existing row, no add needed

    @pytest.mark.asyncio
    async def test_handles_multiple_updates(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        updates = [
            {"notification_type": "donation_received", "channel": "email", "enabled": False},
            {"notification_type": "system_alert", "channel": "in_app", "enabled": False},
            {"notification_type": "gdpr_request", "channel": "email", "enabled": True},
        ]

        result = await update_preferences(db, uuid4(), updates)
        assert len(result) == 3


class TestIsNotificationEnabled:
    """Tests for is_notification_enabled function."""

    @pytest.mark.asyncio
    async def test_returns_true_when_no_preference(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await is_notification_enabled(db, uuid4(), "donation_received", "email")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_true_when_explicitly_enabled(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = True
        db.execute.return_value = mock_result

        result = await is_notification_enabled(db, uuid4(), "donation_received", "email")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_disabled(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = False
        db.execute.return_value = mock_result

        result = await is_notification_enabled(db, uuid4(), "donation_received", "email")
        assert result is False
