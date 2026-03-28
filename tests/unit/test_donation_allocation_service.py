"""Unit tests for donation allocation service.

Tests expense validation, allocation logic, and statistics computation.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.expense import ExpenseCategory
from src.services.donation_allocation_service import (
    MAX_DESCRIPTION_LENGTH,
    MIN_DESCRIPTION_LENGTH,
    AllocationExceedsDonationError,
    DonationNotFoundError,
    ExpenseNotFoundError,
    InvalidExpenseError,
    allocate_donation,
    create_expense,
    get_expense,
    validate_expense_data,
)

# --- Helpers ---


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_donation(**overrides) -> MagicMock:
    """Create a mock Donation."""
    defaults = {
        "id": uuid4(),
        "amount_cents": 10000,
        "status": "completed",
    }
    defaults.update(overrides)
    donation = MagicMock()
    for k, v in defaults.items():
        setattr(donation, k, v)
    return donation


def _make_expense(**overrides) -> MagicMock:
    """Create a mock Expense."""
    defaults = {
        "id": uuid4(),
        "description": "Dog food purchase",
        "category": "food",
        "amount_cents": 5000,
        "currency": "PYG",
        "expense_date": date.today(),
    }
    defaults.update(overrides)
    expense = MagicMock()
    for k, v in defaults.items():
        setattr(expense, k, v)
    return expense


# --- Expense Validation Tests ---


class TestValidateExpenseData:
    """Tests for expense data validation."""

    def test_valid_expense(self) -> None:
        validate_expense_data("Dog food purchase", "food", 5000, date.today())

    def test_description_too_short(self) -> None:
        with pytest.raises(InvalidExpenseError, match="at least"):
            validate_expense_data("Hi", "food", 5000, date.today())

    def test_description_too_long(self) -> None:
        with pytest.raises(InvalidExpenseError, match="at most"):
            validate_expense_data("x" * (MAX_DESCRIPTION_LENGTH + 1), "food", 5000, date.today())

    def test_invalid_category(self) -> None:
        with pytest.raises(InvalidExpenseError, match="Unknown category"):
            validate_expense_data("Valid desc", "spaceship", 5000, date.today())

    def test_zero_amount(self) -> None:
        with pytest.raises(InvalidExpenseError, match="positive"):
            validate_expense_data("Valid desc", "food", 0, date.today())

    def test_negative_amount(self) -> None:
        with pytest.raises(InvalidExpenseError, match="positive"):
            validate_expense_data("Valid desc", "food", -100, date.today())

    def test_future_date(self) -> None:
        future = date.today() + timedelta(days=1)
        with pytest.raises(InvalidExpenseError, match="future"):
            validate_expense_data("Valid desc", "food", 5000, future)

    def test_all_valid_categories(self) -> None:
        for cat in ExpenseCategory:
            validate_expense_data("Valid description", cat.value, 1000, date.today())


# --- Create Expense Tests ---


class TestCreateExpense:
    """Tests for expense creation."""

    @pytest.mark.asyncio
    async def test_creates_expense(self) -> None:
        db = _mock_db()
        await create_expense(
            db,
            description="Vet bill for Luna",
            category="medical",
            amount_cents=15000,
            currency="PYG",
            expense_date=date.today(),
        )
        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_data_raises(self) -> None:
        db = _mock_db()
        with pytest.raises(InvalidExpenseError):
            await create_expense(
                db,
                description="Hi",
                category="food",
                amount_cents=5000,
                currency="PYG",
                expense_date=date.today(),
            )


# --- Get Expense Tests ---


class TestGetExpense:
    """Tests for expense retrieval."""

    @pytest.mark.asyncio
    async def test_found(self) -> None:
        db = _mock_db()
        expense = _make_expense()
        db.get.return_value = expense
        result = await get_expense(db, expense.id)
        assert result == expense

    @pytest.mark.asyncio
    async def test_not_found(self) -> None:
        db = _mock_db()
        db.get.return_value = None
        with pytest.raises(ExpenseNotFoundError):
            await get_expense(db, uuid4())


# --- Allocation Tests ---


class TestAllocateDonation:
    """Tests for donation allocation."""

    @pytest.mark.asyncio
    async def test_successful_allocation(self) -> None:
        db = _mock_db()
        donation = _make_donation(amount_cents=10000)
        expense = _make_expense()

        # db.get called twice: once for donation, once for expense
        db.get.side_effect = [donation, expense]

        # Mock allocated amount query
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        db.execute.return_value = mock_result

        await allocate_donation(
            db,
            donation_id=donation.id,
            expense_id=expense.id,
            amount_cents=5000,
        )
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_donation_not_found(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(DonationNotFoundError):
            await allocate_donation(db, uuid4(), uuid4(), 1000)

    @pytest.mark.asyncio
    async def test_expense_not_found(self) -> None:
        db = _mock_db()
        donation = _make_donation()
        db.get.side_effect = [donation, None]

        with pytest.raises(ExpenseNotFoundError):
            await allocate_donation(db, donation.id, uuid4(), 1000)

    @pytest.mark.asyncio
    async def test_exceeds_available_amount(self) -> None:
        db = _mock_db()
        donation = _make_donation(amount_cents=10000)
        expense = _make_expense()
        db.get.side_effect = [donation, expense]

        # Already allocated 8000 of 10000
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 8000
        db.execute.return_value = mock_result

        with pytest.raises(AllocationExceedsDonationError):
            await allocate_donation(db, donation.id, expense.id, 5000)

    @pytest.mark.asyncio
    async def test_zero_amount_raises(self) -> None:
        db = _mock_db()
        donation = _make_donation()
        expense = _make_expense()
        db.get.side_effect = [donation, expense]

        with pytest.raises(InvalidExpenseError, match="positive"):
            await allocate_donation(db, donation.id, expense.id, 0)

    @pytest.mark.asyncio
    async def test_exact_remaining_amount(self) -> None:
        db = _mock_db()
        donation = _make_donation(amount_cents=10000)
        expense = _make_expense()
        db.get.side_effect = [donation, expense]

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 7000
        db.execute.return_value = mock_result

        await allocate_donation(db, donation.id, expense.id, 3000)
        db.add.assert_called_once()


# --- Exception Tests ---


class TestExceptions:
    """Tests for custom exception classes."""

    def test_expense_not_found_error(self) -> None:
        eid = uuid4()
        error = ExpenseNotFoundError(eid)
        assert error.expense_id == eid
        assert str(eid) in error.message

    def test_donation_not_found_error(self) -> None:
        did = uuid4()
        error = DonationNotFoundError(did)
        assert error.donation_id == did
        assert str(did) in error.message

    def test_allocation_exceeds_error(self) -> None:
        did = uuid4()
        error = AllocationExceedsDonationError(did, 2000, 5000)
        assert error.donation_id == did
        assert error.available_cents == 2000
        assert error.requested_cents == 5000
        assert "5000" in error.message
        assert "2000" in error.message

    def test_invalid_expense_error(self) -> None:
        error = InvalidExpenseError("bad data")
        assert "bad data" in error.message


# --- Constants Tests ---


class TestConstants:
    """Tests for module constants."""

    def test_min_description_length(self) -> None:
        assert MIN_DESCRIPTION_LENGTH == 5

    def test_max_description_length(self) -> None:
        assert MAX_DESCRIPTION_LENGTH == 500

    def test_expense_categories(self) -> None:
        assert ExpenseCategory.FOOD == "food"
        assert ExpenseCategory.MEDICAL == "medical"
        assert ExpenseCategory.TRANSPORT == "transport"
        assert ExpenseCategory.HOUSING == "housing"
        assert ExpenseCategory.OTHER == "other"
        assert len(ExpenseCategory) == 5
