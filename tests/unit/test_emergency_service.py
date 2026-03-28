"""Unit tests for emergency case service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.emergency_service import (
    MAX_DEADLINE_DAYS,
    MIN_DEADLINE_HOURS,
    TITLE_MAX_LENGTH,
    VALID_CURRENCIES,
    VALID_URGENCY,
    EmergencyError,
    EmergencyNotFoundError,
    InvalidDeadlineError,
    InvalidStatusTransitionError,
    create_emergency_case,
    get_emergency_case,
    list_active_emergencies,
    soft_delete_emergency,
    update_emergency_status,
    validate_deadline,
    validate_status_transition,
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
        "animal_id": None,
        "rescuer_id": uuid4(),
        "campaign_id": uuid4(),
        "photos": [],
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
    """Tests for emergency error hierarchy."""

    def test_emergency_error_base(self) -> None:
        err = EmergencyError("test", details="detail")
        assert err.message == "test"
        assert err.details == "detail"

    def test_not_found_error(self) -> None:
        err = EmergencyNotFoundError("abc-123")
        assert "abc-123" in err.details

    def test_invalid_deadline_error(self) -> None:
        err = InvalidDeadlineError("too soon")
        assert err.message == "Invalid deadline"
        assert "too soon" in err.details

    def test_invalid_status_transition(self) -> None:
        err = InvalidStatusTransitionError("active", "expired")
        assert "active" in err.details
        assert "expired" in err.details


# ---------------------------------------------------------------------------
# validate_deadline
# ---------------------------------------------------------------------------


class TestValidateDeadline:
    """Tests for deadline validation."""

    def test_valid_deadline(self) -> None:
        deadline = datetime.now(UTC) + timedelta(days=7)
        validate_deadline(deadline)  # should not raise

    def test_too_soon_raises(self) -> None:
        deadline = datetime.now(UTC) + timedelta(hours=1)
        with pytest.raises(InvalidDeadlineError):
            validate_deadline(deadline)

    def test_exactly_24h_passes(self) -> None:
        deadline = datetime.now(UTC) + timedelta(hours=MIN_DEADLINE_HOURS, minutes=1)
        validate_deadline(deadline)

    def test_too_far_raises(self) -> None:
        deadline = datetime.now(UTC) + timedelta(days=MAX_DEADLINE_DAYS + 1)
        with pytest.raises(InvalidDeadlineError):
            validate_deadline(deadline)


# ---------------------------------------------------------------------------
# validate_status_transition
# ---------------------------------------------------------------------------


class TestValidateStatusTransition:
    """Tests for status transition validation."""

    def test_active_to_funded(self) -> None:
        validate_status_transition("active", "funded")

    def test_active_to_closed(self) -> None:
        validate_status_transition("active", "closed")

    def test_active_to_expired(self) -> None:
        validate_status_transition("active", "expired")

    def test_funded_to_closed(self) -> None:
        validate_status_transition("funded", "closed")

    def test_closed_to_anything_raises(self) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition("closed", "active")

    def test_expired_to_anything_raises(self) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition("expired", "active")

    def test_funded_to_active_raises(self) -> None:
        with pytest.raises(InvalidStatusTransitionError):
            validate_status_transition("funded", "active")


# ---------------------------------------------------------------------------
# create_emergency_case
# ---------------------------------------------------------------------------


class TestCreateEmergencyCase:
    """Tests for create_emergency_case."""

    @pytest.mark.asyncio
    async def test_creates_case_and_campaign(self) -> None:
        db = AsyncMock()
        rescuer_id = uuid4()
        deadline = datetime.now(UTC) + timedelta(days=7)

        case = await create_emergency_case(
            title="Injured dog",
            description="Dog with broken leg",
            rescuer_id=rescuer_id,
            amount_needed_cents=50000,
            deadline=deadline,
            urgency="critical",
            db=db,
        )

        assert case.title == "Injured dog"
        assert case.rescuer_id == rescuer_id
        assert case.amount_needed_cents == 50000
        assert case.urgency == "critical"
        # Two db.add calls: campaign + case
        assert db.add.call_count == 2
        # Two flush calls: campaign + case
        assert db.flush.await_count == 2

    @pytest.mark.asyncio
    async def test_title_too_long_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(EmergencyError, match="Title too long"):
            await create_emergency_case(
                title="A" * (TITLE_MAX_LENGTH + 1),
                description="desc",
                rescuer_id=uuid4(),
                amount_needed_cents=1000,
                deadline=datetime.now(UTC) + timedelta(days=7),
                db=db,
            )

    @pytest.mark.asyncio
    async def test_zero_amount_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(EmergencyError, match="Invalid amount"):
            await create_emergency_case(
                title="Test",
                description="desc",
                rescuer_id=uuid4(),
                amount_needed_cents=0,
                deadline=datetime.now(UTC) + timedelta(days=7),
                db=db,
            )

    @pytest.mark.asyncio
    async def test_invalid_currency_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(EmergencyError, match="Invalid currency"):
            await create_emergency_case(
                title="Test",
                description="desc",
                rescuer_id=uuid4(),
                amount_needed_cents=1000,
                deadline=datetime.now(UTC) + timedelta(days=7),
                currency="EUR",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_invalid_urgency_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(EmergencyError, match="Invalid urgency"):
            await create_emergency_case(
                title="Test",
                description="desc",
                rescuer_id=uuid4(),
                amount_needed_cents=1000,
                deadline=datetime.now(UTC) + timedelta(days=7),
                urgency="low",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_deadline_too_soon_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidDeadlineError):
            await create_emergency_case(
                title="Test",
                description="desc",
                rescuer_id=uuid4(),
                amount_needed_cents=1000,
                deadline=datetime.now(UTC) + timedelta(hours=1),
                db=db,
            )

    @pytest.mark.asyncio
    async def test_valid_currencies(self) -> None:
        for currency in VALID_CURRENCIES:
            db = AsyncMock()
            case = await create_emergency_case(
                title="Test",
                description="desc",
                rescuer_id=uuid4(),
                amount_needed_cents=1000,
                deadline=datetime.now(UTC) + timedelta(days=7),
                currency=currency,
                db=db,
            )
            assert case.currency == currency

    @pytest.mark.asyncio
    async def test_valid_urgencies(self) -> None:
        for urgency in VALID_URGENCY:
            db = AsyncMock()
            case = await create_emergency_case(
                title="Test",
                description="desc",
                rescuer_id=uuid4(),
                amount_needed_cents=1000,
                deadline=datetime.now(UTC) + timedelta(days=7),
                urgency=urgency,
                db=db,
            )
            assert case.urgency == urgency


# ---------------------------------------------------------------------------
# get_emergency_case
# ---------------------------------------------------------------------------


class TestGetEmergencyCase:
    """Tests for get_emergency_case."""

    @pytest.mark.asyncio
    async def test_returns_case(self) -> None:
        case = _make_emergency()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await get_emergency_case(case.id, db)
        assert result.id == case.id

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(EmergencyNotFoundError):
            await get_emergency_case(uuid4(), db)


# ---------------------------------------------------------------------------
# update_emergency_status
# ---------------------------------------------------------------------------


class TestUpdateEmergencyStatus:
    """Tests for update_emergency_status."""

    @pytest.mark.asyncio
    async def test_updates_status(self) -> None:
        case = _make_emergency(status="active")
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await update_emergency_status(emergency_id=case.id, new_status="funded", db=db)
        assert result.status == "funded"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self) -> None:
        case = _make_emergency(status="closed")
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        with pytest.raises(InvalidStatusTransitionError):
            await update_emergency_status(emergency_id=case.id, new_status="active", db=db)


# ---------------------------------------------------------------------------
# soft_delete_emergency
# ---------------------------------------------------------------------------


class TestSoftDeleteEmergency:
    """Tests for soft_delete_emergency."""

    @pytest.mark.asyncio
    async def test_sets_is_deleted(self) -> None:
        case = _make_emergency(is_deleted=False)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = case
        db.execute.return_value = mock_result

        result = await soft_delete_emergency(emergency_id=case.id, db=db)
        assert result.is_deleted is True


# ---------------------------------------------------------------------------
# list_active_emergencies
# ---------------------------------------------------------------------------


class TestListActiveEmergencies:
    """Tests for list_active_emergencies."""

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        cases = [_make_emergency(), _make_emergency()]
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = cases
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await list_active_emergencies(db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await list_active_emergencies(db)
        assert result == []
