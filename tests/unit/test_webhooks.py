"""Unit tests for Stripe webhook handler logic.

Tests the internal handler functions and helper utilities without requiring
a real database or HTTP requests. Mocks SQLAlchemy session and Stripe SDK.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.api.webhooks import (
    EVENT_CHARGE_REFUNDED,
    EVENT_PAYMENT_INTENT_FAILED,
    EVENT_PAYMENT_INTENT_SUCCEEDED,
    HANDLED_EVENT_TYPES,
    _extract_payment_intent_id_from_object,
    _handle_charge_refunded,
    _handle_payment_failed,
    _handle_payment_succeeded,
)
from src.db.models.donation import DonationStatus


class TestExtractPaymentIntentId:
    """Tests for _extract_payment_intent_id_from_object helper."""

    def test_extracts_id_from_payment_intent_succeeded(self) -> None:
        data_obj = {"id": "pi_123abc", "amount": 5000}
        result = _extract_payment_intent_id_from_object(data_obj, EVENT_PAYMENT_INTENT_SUCCEEDED)
        assert result == "pi_123abc"

    def test_extracts_id_from_payment_intent_failed(self) -> None:
        data_obj = {"id": "pi_456def", "amount": 3000}
        result = _extract_payment_intent_id_from_object(data_obj, EVENT_PAYMENT_INTENT_FAILED)
        assert result == "pi_456def"

    def test_extracts_payment_intent_from_charge_refunded(self) -> None:
        data_obj = {"id": "ch_789ghi", "payment_intent": "pi_123abc"}
        result = _extract_payment_intent_id_from_object(data_obj, EVENT_CHARGE_REFUNDED)
        assert result == "pi_123abc"

    def test_returns_none_for_unknown_event_type(self) -> None:
        data_obj = {"id": "pi_123abc"}
        result = _extract_payment_intent_id_from_object(data_obj, "unknown.event_type")
        assert result is None

    def test_returns_none_when_id_missing(self) -> None:
        data_obj = {"amount": 5000}
        result = _extract_payment_intent_id_from_object(data_obj, EVENT_PAYMENT_INTENT_SUCCEEDED)
        assert result is None

    def test_returns_none_when_payment_intent_missing_from_charge(self) -> None:
        data_obj = {"id": "ch_789ghi"}
        result = _extract_payment_intent_id_from_object(data_obj, EVENT_CHARGE_REFUNDED)
        assert result is None


class TestHandledEventTypes:
    """Verify the set of handled event types."""

    def test_includes_succeeded(self) -> None:
        assert EVENT_PAYMENT_INTENT_SUCCEEDED in HANDLED_EVENT_TYPES

    def test_includes_failed(self) -> None:
        assert EVENT_PAYMENT_INTENT_FAILED in HANDLED_EVENT_TYPES

    def test_includes_refunded(self) -> None:
        assert EVENT_CHARGE_REFUNDED in HANDLED_EVENT_TYPES

    def test_does_not_include_random_event(self) -> None:
        assert "customer.created" not in HANDLED_EVENT_TYPES


class TestHandlePaymentSucceeded:
    """Tests for _handle_payment_succeeded handler."""

    @pytest.mark.asyncio
    async def test_marks_donation_completed(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.PENDING.value
        donation.amount_cents = 5000
        donation.currency = "EUR"
        donation.donor_id = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        result = await _handle_payment_succeeded(db, "pi_123", None)

        assert result == "completed"
        assert donation.status == DonationStatus.COMPLETED.value
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_already_completed_for_duplicate(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.COMPLETED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        result = await _handle_payment_succeeded(db, "pi_123", None)

        assert result == "already_completed"
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_donation_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await _handle_payment_succeeded(db, "pi_unknown", None)

        assert result == "donation_not_found"

    @pytest.mark.asyncio
    async def test_publishes_domain_event_on_success(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.PENDING.value
        donation.amount_cents = 5000
        donation.currency = "EUR"
        donation.donor_id = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        event_bus = AsyncMock()
        event_bus.is_running = True

        result = await _handle_payment_succeeded(db, "pi_123", event_bus)

        assert result == "completed"
        event_bus.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_skips_event_bus_when_not_running(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.PENDING.value
        donation.amount_cents = 5000
        donation.currency = "EUR"
        donation.donor_id = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        event_bus = AsyncMock()
        event_bus.is_running = False

        result = await _handle_payment_succeeded(db, "pi_123", event_bus)

        assert result == "completed"
        event_bus.publish.assert_not_awaited()


class TestHandlePaymentFailed:
    """Tests for _handle_payment_failed handler."""

    @pytest.mark.asyncio
    async def test_marks_donation_failed(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.PENDING.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        result = await _handle_payment_failed(db, "pi_123")

        assert result == "failed"
        assert donation.status == DonationStatus.FAILED.value
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_already_failed_for_duplicate(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.FAILED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        result = await _handle_payment_failed(db, "pi_123")

        assert result == "already_failed"

    @pytest.mark.asyncio
    async def test_returns_donation_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await _handle_payment_failed(db, "pi_unknown")

        assert result == "donation_not_found"


class TestHandleChargeRefunded:
    """Tests for _handle_charge_refunded handler."""

    @pytest.mark.asyncio
    async def test_marks_donation_refunded(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.COMPLETED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        result = await _handle_charge_refunded(db, "pi_123")

        assert result == "refunded"
        assert donation.status == DonationStatus.REFUNDED.value
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_already_refunded_for_duplicate(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.REFUNDED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        result = await _handle_charge_refunded(db, "pi_123")

        assert result == "already_refunded"

    @pytest.mark.asyncio
    async def test_returns_donation_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await _handle_charge_refunded(db, "pi_unknown")

        assert result == "donation_not_found"
