"""Unit tests for src/api/public_emergencies.py."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from src.api.public_emergencies import (
    _serialise,
    get_emergency_public,
    list_active_emergencies_public,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_emergency(**overrides):
    """Create a mock EmergencyCase object."""
    defaults = {
        "id": uuid4(),
        "title": "Perro atropellado necesita cirugia",
        "description": "Encontrado en Ruta 1 con fractura expuesta",
        "photos": ["photo1.jpg", "photo2.jpg"],
        "amount_needed_cents": 500_000,
        "amount_raised_cents": 250_000,
        "currency": "PYG",
        "deadline": datetime(2026, 4, 15, 12, 0, 0, tzinfo=UTC),
        "status": "active",
        "urgency": "critical",
        "created_at": datetime(2026, 3, 25, 10, 0, 0, tzinfo=UTC),
        "is_deleted": False,
    }
    defaults.update(overrides)
    mock = MagicMock(**defaults)
    return mock


# ---------------------------------------------------------------------------
# Test _serialise helper
# ---------------------------------------------------------------------------


class TestSerialise:
    """Tests for the _serialise helper function."""

    def test_calculates_progress_percentage(self) -> None:
        emergency = _make_emergency(amount_needed_cents=1000, amount_raised_cents=750)
        result = _serialise(emergency)
        assert result["progress_pct"] == 75

    def test_caps_progress_at_100(self) -> None:
        emergency = _make_emergency(amount_needed_cents=1000, amount_raised_cents=1500)
        result = _serialise(emergency)
        assert result["progress_pct"] == 100

    def test_handles_zero_raised(self) -> None:
        emergency = _make_emergency(amount_needed_cents=1000, amount_raised_cents=0)
        result = _serialise(emergency)
        assert result["progress_pct"] == 0

    def test_handles_none_raised(self) -> None:
        emergency = _make_emergency(amount_needed_cents=1000, amount_raised_cents=None)
        result = _serialise(emergency)
        assert result["progress_pct"] == 0

    def test_handles_none_needed_defaults_to_one(self) -> None:
        emergency = _make_emergency(amount_needed_cents=None, amount_raised_cents=50)
        result = _serialise(emergency)
        # With needed=1, raised=50 => min(100, 5000) = 100
        assert result["progress_pct"] == 100

    def test_serialises_all_fields(self) -> None:
        eid = uuid4()
        emergency = _make_emergency(id=eid, title="Test Emergency")
        result = _serialise(emergency)

        assert result["id"] == eid
        assert result["title"] == "Test Emergency"
        assert result["description"] == "Encontrado en Ruta 1 con fractura expuesta"
        assert result["photos"] == ["photo1.jpg", "photo2.jpg"]
        assert result["currency"] == "PYG"
        assert result["status"] == "active"
        assert result["urgency"] == "critical"
        assert isinstance(result["deadline"], str)
        assert isinstance(result["created_at"], str)

    def test_empty_photos_returns_empty_list(self) -> None:
        emergency = _make_emergency(photos=None)
        result = _serialise(emergency)
        assert result["photos"] == []


# ---------------------------------------------------------------------------
# Test list_active_emergencies_public
# ---------------------------------------------------------------------------


class TestListActiveEmergenciesPublic:
    """Tests for the GET /active endpoint."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        e1 = _make_emergency(title="Emergency 1")
        e2 = _make_emergency(title="Emergency 2")

        mock_db = AsyncMock()
        # First call: count query
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 2
        # Second call: select query
        mock_select_result = MagicMock()
        mock_select_result.scalars.return_value.all.return_value = [e1, e2]

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_select_result])

        result = await list_active_emergencies_public(limit=10, offset=0, db=mock_db)

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["items"][0]["title"] == "Emergency 1"

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_emergencies(self) -> None:
        mock_db = AsyncMock()
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        mock_select_result = MagicMock()
        mock_select_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[mock_count_result, mock_select_result])

        result = await list_active_emergencies_public(limit=10, offset=0, db=mock_db)

        assert result["total"] == 0
        assert result["items"] == []


# ---------------------------------------------------------------------------
# Test get_emergency_public
# ---------------------------------------------------------------------------


class TestGetEmergencyPublic:
    """Tests for the GET /{emergency_id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_emergency_detail(self) -> None:
        eid = uuid4()
        emergency = _make_emergency(id=eid, title="Detail Case")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = emergency
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await get_emergency_public(emergency_id=eid, db=mock_db)

        assert result["id"] == eid
        assert result["title"] == "Detail Case"

    @pytest.mark.asyncio
    async def test_raises_404_for_nonexistent(self) -> None:
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_emergency_public(emergency_id=uuid4(), db=mock_db)

        assert exc_info.value.status_code == 404
