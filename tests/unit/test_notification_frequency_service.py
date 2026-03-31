"""Unit tests for notification channel frequency service.

Tests frequency CRUD, defaults, and is_immediate helper
with mocked database sessions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.notification_channel_frequency import NotificationFrequency
from src.services.notification_frequency_service import (
    SUPPORTED_CHANNELS,
    get_channel_frequencies,
    get_frequency,
    is_immediate,
    set_channel_frequency,
)


class TestGetChannelFrequencies:
    """Tests for get_channel_frequencies function."""

    @pytest.mark.asyncio
    async def test_returns_all_channels_with_defaults_for_new_user(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_channel_frequencies(db, uuid4())

        assert len(result) == len(SUPPORTED_CHANNELS)
        channels_returned = {r["channel"] for r in result}
        assert channels_returned == set(SUPPORTED_CHANNELS)
        for entry in result:
            assert entry["frequency"] == NotificationFrequency.IMMEDIATE

    @pytest.mark.asyncio
    async def test_respects_stored_frequency(self) -> None:
        db = AsyncMock()
        row = MagicMock()
        row.channel = "email"
        row.frequency = "daily_digest"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [row]
        db.execute.return_value = mock_result

        result = await get_channel_frequencies(db, uuid4())

        email_entry = next(r for r in result if r["channel"] == "email")
        assert email_entry["frequency"] == "daily_digest"

    @pytest.mark.asyncio
    async def test_missing_channel_defaults_to_immediate(self) -> None:
        db = AsyncMock()
        # Only email row present — in_app should default
        row = MagicMock()
        row.channel = "email"
        row.frequency = "weekly"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [row]
        db.execute.return_value = mock_result

        result = await get_channel_frequencies(db, uuid4())

        in_app_entry = next(r for r in result if r["channel"] == "in_app")
        assert in_app_entry["frequency"] == NotificationFrequency.IMMEDIATE


class TestSetChannelFrequency:
    """Tests for set_channel_frequency function."""

    @pytest.mark.asyncio
    async def test_creates_new_row_when_missing(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        db.flush = AsyncMock()

        result = await set_channel_frequency(db, uuid4(), "email", "daily_digest")

        db.add.assert_called_once()
        assert result.frequency == "daily_digest"
        assert result.channel == "email"

    @pytest.mark.asyncio
    async def test_updates_existing_row(self) -> None:
        db = AsyncMock()
        existing_row = MagicMock()
        existing_row.frequency = "immediate"
        existing_row.channel = "email"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_row
        db.execute.return_value = mock_result
        db.flush = AsyncMock()

        await set_channel_frequency(db, uuid4(), "email", "weekly")

        assert existing_row.frequency == "weekly"
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_flushes_after_upsert(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result
        db.flush = AsyncMock()

        await set_channel_frequency(db, uuid4(), "in_app", "immediate")

        db.flush.assert_awaited_once()


class TestGetFrequency:
    """Tests for get_frequency function."""

    @pytest.mark.asyncio
    async def test_returns_stored_frequency(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "daily_digest"
        db.execute.return_value = mock_result

        freq = await get_frequency(db, uuid4(), "email")
        assert freq == "daily_digest"

    @pytest.mark.asyncio
    async def test_defaults_to_immediate_when_not_set(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        freq = await get_frequency(db, uuid4(), "email")
        assert freq == NotificationFrequency.IMMEDIATE


class TestIsImmediate:
    """Tests for is_immediate function."""

    @pytest.mark.asyncio
    async def test_returns_true_for_immediate(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "immediate"
        db.execute.return_value = mock_result

        result = await is_immediate(db, uuid4(), "email")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_for_daily_digest(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "daily_digest"
        db.execute.return_value = mock_result

        result = await is_immediate(db, uuid4(), "email")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_for_weekly(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = "weekly"
        db.execute.return_value = mock_result

        result = await is_immediate(db, uuid4(), "email")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_not_set(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await is_immediate(db, uuid4(), "in_app")
        assert result is True
