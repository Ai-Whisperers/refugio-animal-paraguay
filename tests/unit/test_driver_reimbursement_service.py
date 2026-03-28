"""Unit tests for driver reimbursement service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.driver_reimbursement_service import (
    DEFAULT_PAGE_SIZE,
    VALID_TRANSITIONS,
    InvalidReimbursementError,
    InvalidStatusTransitionError,
    ReimbursementError,
    ReimbursementNotFoundError,
    create_reimbursement,
    delete_reimbursement,
    get_reimbursement,
    list_reimbursements,
    mark_paid,
    review_reimbursement,
)

# --- Test Error Classes ---


class TestErrorClasses:
    """Tests for error hierarchy."""

    def test_reimbursement_error_is_exception(self) -> None:
        assert isinstance(ReimbursementError("test"), Exception)

    def test_not_found_is_reimbursement_error(self) -> None:
        assert isinstance(ReimbursementNotFoundError("x"), ReimbursementError)

    def test_invalid_is_reimbursement_error(self) -> None:
        assert isinstance(InvalidReimbursementError("x"), ReimbursementError)

    def test_invalid_transition_is_reimbursement_error(self) -> None:
        assert isinstance(InvalidStatusTransitionError("x"), ReimbursementError)


# --- Test Status Transitions ---


class TestStatusTransitions:
    """Tests for valid transition map."""

    def test_pending_can_be_approved(self) -> None:
        assert "approved" in VALID_TRANSITIONS["pending"]

    def test_pending_can_be_rejected(self) -> None:
        assert "rejected" in VALID_TRANSITIONS["pending"]

    def test_approved_can_be_paid(self) -> None:
        assert "paid" in VALID_TRANSITIONS["approved"]

    def test_rejected_is_terminal(self) -> None:
        assert len(VALID_TRANSITIONS["rejected"]) == 0

    def test_paid_is_terminal(self) -> None:
        assert len(VALID_TRANSITIONS["paid"]) == 0


# --- Helper ---


def _mock_reimbursement(status="pending", **kwargs):
    """Create a mock driver reimbursement."""
    r = MagicMock()
    r.id = kwargs.get("id", uuid4())
    r.transport_request_id = kwargs.get("transport_request_id", uuid4())
    r.driver_id = kwargs.get("driver_id", uuid4())
    r.expense_type = kwargs.get("expense_type", "fuel")
    r.amount = kwargs.get("amount", 50000.00)
    r.currency = kwargs.get("currency", "PYG")
    r.description = kwargs.get("description")
    r.receipt_url = kwargs.get("receipt_url")
    r.status = status
    r.reviewed_by = kwargs.get("reviewed_by")
    r.reviewed_at = kwargs.get("reviewed_at")
    r.rejection_reason = kwargs.get("rejection_reason")
    r.created_at = kwargs.get("created_at")
    r.updated_at = kwargs.get("updated_at")
    return r


# --- Test create_reimbursement ---


class TestCreateReimbursement:
    """Tests for creating reimbursements."""

    @pytest.mark.asyncio
    async def test_creates_successfully(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement()

        async def fake_refresh(obj):
            for attr in (
                "id",
                "transport_request_id",
                "driver_id",
                "expense_type",
                "amount",
                "currency",
                "description",
                "receipt_url",
                "status",
                "reviewed_by",
                "reviewed_at",
                "rejection_reason",
                "created_at",
                "updated_at",
            ):
                setattr(obj, attr, getattr(mock_r, attr))

        db.refresh = fake_refresh

        result = await create_reimbursement(
            db=db,
            transport_request_id=uuid4(),
            driver_id=uuid4(),
            expense_type="fuel",
            amount=50000.00,
        )

        assert result["expense_type"] == "fuel"
        assert db.add.called
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_invalid_expense_type_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidReimbursementError, match="Invalid expense type"):
            await create_reimbursement(
                db=db,
                transport_request_id=uuid4(),
                driver_id=uuid4(),
                expense_type="bribes",
                amount=100,
            )

    @pytest.mark.asyncio
    async def test_invalid_currency_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidReimbursementError, match="Invalid currency"):
            await create_reimbursement(
                db=db,
                transport_request_id=uuid4(),
                driver_id=uuid4(),
                expense_type="fuel",
                amount=100,
                currency="BTC",
            )

    @pytest.mark.asyncio
    async def test_zero_amount_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidReimbursementError, match="greater than zero"):
            await create_reimbursement(
                db=db,
                transport_request_id=uuid4(),
                driver_id=uuid4(),
                expense_type="fuel",
                amount=0,
            )

    @pytest.mark.asyncio
    async def test_negative_amount_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidReimbursementError, match="greater than zero"):
            await create_reimbursement(
                db=db,
                transport_request_id=uuid4(),
                driver_id=uuid4(),
                expense_type="fuel",
                amount=-50,
            )


# --- Test get_reimbursement ---


class TestGetReimbursement:
    """Tests for fetching reimbursements."""

    @pytest.mark.asyncio
    async def test_returns_reimbursement(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        result = await get_reimbursement(db, mock_r.id)
        assert result["id"] == mock_r.id

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(ReimbursementNotFoundError):
            await get_reimbursement(db, uuid4())


# --- Test list_reimbursements ---


class TestListReimbursements:
    """Tests for listing reimbursements."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 1

        mock_r = _mock_reimbursement()
        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = [mock_r]
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_reimbursements(db)
        assert result["total"] == 1
        assert len(result["reimbursements"]) == 1
        assert result["limit"] == DEFAULT_PAGE_SIZE

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        list_result = MagicMock()
        list_scalars = MagicMock()
        list_scalars.all.return_value = []
        list_result.scalars.return_value = list_scalars

        db.execute.side_effect = [count_result, list_result]

        result = await list_reimbursements(db)
        assert result["total"] == 0
        assert result["reimbursements"] == []


# --- Test review_reimbursement ---


class TestReviewReimbursement:
    """Tests for reviewing (approve/reject) reimbursements."""

    @pytest.mark.asyncio
    async def test_approve_pending(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement(status="pending")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await review_reimbursement(db, mock_r.id, uuid4(), "approved")
        assert mock_r.status == "approved"
        assert mock_r.reviewed_by is not None

    @pytest.mark.asyncio
    async def test_reject_pending_with_reason(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement(status="pending")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await review_reimbursement(
            db, mock_r.id, uuid4(), "rejected", rejection_reason="No receipt"
        )
        assert mock_r.status == "rejected"
        assert mock_r.rejection_reason == "No receipt"

    @pytest.mark.asyncio
    async def test_invalid_transition_raises(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement(status="paid")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        with pytest.raises(InvalidStatusTransitionError, match="Cannot transition"):
            await review_reimbursement(db, mock_r.id, uuid4(), "approved")

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(ReimbursementNotFoundError):
            await review_reimbursement(db, uuid4(), uuid4(), "approved")


# --- Test mark_paid ---


class TestMarkPaid:
    """Tests for marking reimbursements as paid."""

    @pytest.mark.asyncio
    async def test_marks_approved_as_paid(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement(status="approved")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            pass

        db.refresh = fake_refresh

        await mark_paid(db, mock_r.id, uuid4())
        assert mock_r.status == "paid"

    @pytest.mark.asyncio
    async def test_cannot_pay_pending(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement(status="pending")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        with pytest.raises(InvalidStatusTransitionError):
            await mark_paid(db, mock_r.id, uuid4())


# --- Test delete_reimbursement ---


class TestDeleteReimbursement:
    """Tests for deleting reimbursements."""

    @pytest.mark.asyncio
    async def test_deletes_pending(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement(status="pending")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        await delete_reimbursement(db, mock_r.id)
        db.delete.assert_called_once_with(mock_r)

    @pytest.mark.asyncio
    async def test_cannot_delete_approved(self) -> None:
        db = AsyncMock()
        mock_r = _mock_reimbursement(status="approved")

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_r
        db.execute.return_value = result_mock

        with pytest.raises(InvalidReimbursementError, match="Cannot delete"):
            await delete_reimbursement(db, mock_r.id)

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(ReimbursementNotFoundError):
            await delete_reimbursement(db, uuid4())
