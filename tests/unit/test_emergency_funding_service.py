"""Unit tests for emergency funding service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.emergency_funding_service import (
    EmergencyNotFoundError,
    FundingCheckError,
    batch_check_active_emergencies,
    check_and_update_funding,
    get_funding_progress,
    process_donation_for_emergency,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_emergency(**overrides):
    """Create a mock EmergencyCase with sensible defaults."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "title": "Injured dog found",
        "description": "Dog with broken leg near market",
        "amount_needed_cents": 50000,
        "amount_raised_cents": 0,
        "currency": "USD",
        "deadline": now + timedelta(days=7),
        "status": "active",
        "urgency": "high",
        "is_deleted": False,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for funding error hierarchy."""

    def test_funding_check_error_base(self) -> None:
        err = FundingCheckError("test", details="detail")
        assert err.message == "test"
        assert err.details == "detail"

    def test_emergency_not_found(self) -> None:
        err = EmergencyNotFoundError("abc-123")
        assert "abc-123" in err.details


# ---------------------------------------------------------------------------
# check_and_update_funding
# ---------------------------------------------------------------------------


class TestCheckAndUpdateFunding:
    """Tests for check_and_update_funding."""

    @pytest.mark.asyncio
    async def test_not_funded_no_change(self) -> None:
        case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=20000)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await check_and_update_funding(emergency_id=case.id, db=db)
        assert result["is_funded"] is False
        assert result["action_taken"] == "no_change"
        assert result["new_status"] == "active"

    @pytest.mark.asyncio
    async def test_fully_funded_transitions(self) -> None:
        case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=50000)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await check_and_update_funding(emergency_id=case.id, db=db)
        assert result["is_funded"] is True
        assert result["action_taken"] == "status_changed_to_funded"
        assert result["new_status"] == "funded"
        assert case.status == "funded"

    @pytest.mark.asyncio
    async def test_overfunded_transitions(self) -> None:
        case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=75000)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await check_and_update_funding(emergency_id=case.id, db=db)
        assert result["is_funded"] is True
        assert result["action_taken"] == "status_changed_to_funded"

    @pytest.mark.asyncio
    async def test_already_funded_no_change(self) -> None:
        case = _make_emergency(
            status="funded",
            amount_needed_cents=50000,
            amount_raised_cents=50000,
        )
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await check_and_update_funding(emergency_id=case.id, db=db)
        assert result["is_funded"] is True
        assert result["action_taken"] == "no_change"

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(EmergencyNotFoundError):
            await check_and_update_funding(emergency_id=uuid4(), db=db)


# ---------------------------------------------------------------------------
# process_donation_for_emergency
# ---------------------------------------------------------------------------


class TestProcessDonationForEmergency:
    """Tests for process_donation_for_emergency."""

    @pytest.mark.asyncio
    async def test_records_donation_and_checks_funding(self) -> None:
        case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=40000)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await process_donation_for_emergency(
            emergency_id=case.id,
            donation_amount_cents=10000,
            db=db,
        )
        # 40000 + 10000 = 50000, should be funded
        assert case.amount_raised_cents == 50000
        assert result["is_funded"] is True

    @pytest.mark.asyncio
    async def test_partial_donation_no_close(self) -> None:
        case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=10000)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await process_donation_for_emergency(
            emergency_id=case.id,
            donation_amount_cents=5000,
            db=db,
        )
        assert case.amount_raised_cents == 15000
        assert result["is_funded"] is False

    @pytest.mark.asyncio
    async def test_zero_donation_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(FundingCheckError, match="Invalid donation"):
            await process_donation_for_emergency(
                emergency_id=uuid4(),
                donation_amount_cents=0,
                db=db,
            )

    @pytest.mark.asyncio
    async def test_negative_donation_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(FundingCheckError, match="Invalid donation"):
            await process_donation_for_emergency(
                emergency_id=uuid4(),
                donation_amount_cents=-100,
                db=db,
            )

    @pytest.mark.asyncio
    async def test_closed_emergency_rejects(self) -> None:
        case = _make_emergency(status="closed")
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        with pytest.raises(FundingCheckError, match="not accepting"):
            await process_donation_for_emergency(
                emergency_id=case.id,
                donation_amount_cents=1000,
                db=db,
            )

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(EmergencyNotFoundError):
            await process_donation_for_emergency(
                emergency_id=uuid4(),
                donation_amount_cents=1000,
                db=db,
            )


# ---------------------------------------------------------------------------
# batch_check_active_emergencies
# ---------------------------------------------------------------------------


class TestBatchCheckActiveEmergencies:
    """Tests for batch_check_active_emergencies."""

    @pytest.mark.asyncio
    async def test_funds_and_expires(self) -> None:
        funded_case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=60000)
        expired_case = _make_emergency(deadline=datetime.now(UTC) - timedelta(days=1))

        db = AsyncMock()
        # First call: funded cases, second call: expired cases
        funded_result = MagicMock()
        funded_scalars = MagicMock()
        funded_scalars.all.return_value = [funded_case]
        funded_result.scalars.return_value = funded_scalars

        expired_result = MagicMock()
        expired_scalars = MagicMock()
        expired_scalars.all.return_value = [expired_case]
        expired_result.scalars.return_value = expired_scalars

        db.execute.side_effect = [funded_result, expired_result]

        results = await batch_check_active_emergencies(db)
        assert len(results) == 2
        assert funded_case.status == "funded"
        assert expired_case.status == "expired"

    @pytest.mark.asyncio
    async def test_no_updates(self) -> None:
        db = AsyncMock()
        empty_result = MagicMock()
        empty_scalars = MagicMock()
        empty_scalars.all.return_value = []
        empty_result.scalars.return_value = empty_scalars
        db.execute.side_effect = [empty_result, empty_result]

        results = await batch_check_active_emergencies(db)
        assert results == []

    @pytest.mark.asyncio
    async def test_only_funded(self) -> None:
        case = _make_emergency(amount_needed_cents=1000, amount_raised_cents=2000)
        db = AsyncMock()

        funded_result = MagicMock()
        funded_scalars = MagicMock()
        funded_scalars.all.return_value = [case]
        funded_result.scalars.return_value = funded_scalars

        empty_result = MagicMock()
        empty_scalars = MagicMock()
        empty_scalars.all.return_value = []
        empty_result.scalars.return_value = empty_scalars

        db.execute.side_effect = [funded_result, empty_result]

        results = await batch_check_active_emergencies(db)
        assert len(results) == 1
        assert results[0]["action_taken"] == "batch_funded"


# ---------------------------------------------------------------------------
# get_funding_progress
# ---------------------------------------------------------------------------


class TestGetFundingProgress:
    """Tests for get_funding_progress."""

    @pytest.mark.asyncio
    async def test_returns_progress(self) -> None:
        case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=25000)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        progress = await get_funding_progress(emergency_id=case.id, db=db)
        assert progress["funding_percentage"] == 50.0
        assert progress["amount_remaining_cents"] == 25000
        assert progress["is_fully_funded"] is False

    @pytest.mark.asyncio
    async def test_fully_funded_progress(self) -> None:
        case = _make_emergency(amount_needed_cents=50000, amount_raised_cents=75000)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        progress = await get_funding_progress(emergency_id=case.id, db=db)
        assert progress["funding_percentage"] == 100
        assert progress["amount_remaining_cents"] == 0
        assert progress["is_fully_funded"] is True

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(EmergencyNotFoundError):
            await get_funding_progress(emergency_id=uuid4(), db=db)
