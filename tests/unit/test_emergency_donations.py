"""Unit tests for src/api/emergency_donations.py."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from src.api.emergency_donations import (
    _calc_progress,
    _suggested_amounts,
    create_emergency_donation,
    get_emergency_donate_info,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_emergency(**overrides):
    """Create a mock EmergencyCase object."""
    defaults = {
        "id": uuid4(),
        "title": "Gato herido necesita atencion",
        "description": "Encontrado en el parque con herida abierta",
        "photos": ["photo1.jpg"],
        "amount_needed_cents": 200_000,
        "amount_raised_cents": 80_000,
        "currency": "USD",
        "deadline": datetime(2026, 4, 10, 12, 0, 0, tzinfo=UTC),
        "status": "active",
        "urgency": "high",
        "is_deleted": False,
        "created_at": datetime(2026, 3, 25, 10, 0, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


def _mock_db_with_emergency(emergency):
    """Create a mock async db session that returns the given emergency."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = emergency
    mock_db.execute = AsyncMock(return_value=mock_result)
    return mock_db


# ---------------------------------------------------------------------------
# Test _calc_progress helper
# ---------------------------------------------------------------------------


class TestCalcProgress:
    """Tests for the _calc_progress helper."""

    def test_normal_percentage(self) -> None:
        assert _calc_progress(1000, 500) == 50

    def test_caps_at_100(self) -> None:
        assert _calc_progress(1000, 1500) == 100

    def test_zero_needed_returns_100(self) -> None:
        assert _calc_progress(0, 500) == 100

    def test_zero_raised(self) -> None:
        assert _calc_progress(1000, 0) == 0

    def test_negative_needed_returns_100(self) -> None:
        assert _calc_progress(-100, 50) == 100


# ---------------------------------------------------------------------------
# Test _suggested_amounts helper
# ---------------------------------------------------------------------------


class TestSuggestedAmounts:
    """Tests for the _suggested_amounts helper."""

    def test_returns_sorted_unique_amounts(self) -> None:
        result = _suggested_amounts(100_000)
        assert result == sorted(result)
        assert len(result) == len(set(result))

    def test_includes_percentage_based_amounts(self) -> None:
        result = _suggested_amounts(100_000)
        # 10% = 10000, 25% = 25000, 50% = 50000, 100% = 100000
        assert 10_000 in result
        assert 25_000 in result
        assert 50_000 in result

    def test_zero_remaining_returns_fixed(self) -> None:
        result = _suggested_amounts(0)
        assert result == [5_000, 10_000, 25_000, 50_000]

    def test_max_six_amounts(self) -> None:
        result = _suggested_amounts(500_000)
        assert len(result) <= 6


# ---------------------------------------------------------------------------
# Test get_emergency_donate_info endpoint
# ---------------------------------------------------------------------------


class TestGetEmergencyDonateInfo:
    """Tests for the GET /donate/info endpoint."""

    @pytest.mark.asyncio
    async def test_returns_emergency_info(self) -> None:
        eid = uuid4()
        emergency = _make_emergency(id=eid, amount_needed_cents=100_000, amount_raised_cents=40_000)
        mock_db = _mock_db_with_emergency(emergency)

        result = await get_emergency_donate_info(emergency_id=eid, db=mock_db)

        assert result["id"] == eid
        assert result["remaining_cents"] == 60_000
        assert result["progress_pct"] == 40
        assert isinstance(result["suggested_amounts_cents"], list)

    @pytest.mark.asyncio
    async def test_404_for_missing_emergency(self) -> None:
        mock_db = _mock_db_with_emergency(None)

        with pytest.raises(HTTPException) as exc_info:
            await get_emergency_donate_info(emergency_id=uuid4(), db=mock_db)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test create_emergency_donation endpoint
# ---------------------------------------------------------------------------


class TestCreateEmergencyDonation:
    """Tests for the POST /donate endpoint."""

    @pytest.mark.asyncio
    async def test_creates_donation_successfully(self) -> None:
        eid = uuid4()
        emergency = _make_emergency(
            id=eid,
            amount_needed_cents=100_000,
            amount_raised_cents=50_000,
            status="active",
        )
        mock_db = _mock_db_with_emergency(emergency)

        payload = MagicMock()
        payload.amount_cents = 20_000
        payload.currency.value = "USD"
        payload.payment_method.value = "stripe"
        payload.notes = None
        payload.donor_email = None
        payload.donor_name = None

        result = await create_emergency_donation(emergency_id=eid, payload=payload, db=mock_db)

        assert result["amount_cents"] == 20_000
        assert result["new_total_raised_cents"] == 70_000
        assert result["new_progress_pct"] == 70

    @pytest.mark.asyncio
    async def test_auto_funds_when_goal_reached(self) -> None:
        eid = uuid4()
        emergency = _make_emergency(
            id=eid,
            amount_needed_cents=100_000,
            amount_raised_cents=80_000,
            status="active",
        )
        mock_db = _mock_db_with_emergency(emergency)

        payload = MagicMock()
        payload.amount_cents = 30_000
        payload.currency.value = "USD"
        payload.payment_method.value = "stripe"
        payload.notes = None

        result = await create_emergency_donation(emergency_id=eid, payload=payload, db=mock_db)

        assert result["new_progress_pct"] == 100
        assert emergency.status == "funded"

    @pytest.mark.asyncio
    async def test_rejects_closed_emergency(self) -> None:
        emergency = _make_emergency(status="closed")
        mock_db = _mock_db_with_emergency(emergency)

        payload = MagicMock()
        payload.amount_cents = 10_000
        payload.currency.value = "USD"
        payload.payment_method.value = "stripe"
        payload.notes = None

        with pytest.raises(HTTPException) as exc_info:
            await create_emergency_donation(emergency_id=uuid4(), payload=payload, db=mock_db)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_404_for_missing_emergency(self) -> None:
        mock_db = _mock_db_with_emergency(None)

        payload = MagicMock()
        payload.amount_cents = 10_000

        with pytest.raises(HTTPException) as exc_info:
            await create_emergency_donation(emergency_id=uuid4(), payload=payload, db=mock_db)

        assert exc_info.value.status_code == 404
