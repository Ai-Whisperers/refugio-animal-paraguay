"""Unit tests for subscription-related webhook handler logic.

Tests the internal handler functions for invoice and subscription events
without requiring a real database or HTTP requests.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.api.webhooks import (
    EVENT_INVOICE_PAYMENT_FAILED,
    EVENT_INVOICE_PAYMENT_SUCCEEDED,
    EVENT_SUBSCRIPTION_DELETED,
    HANDLED_EVENT_TYPES,
    _handle_invoice_payment_failed,
    _handle_invoice_payment_succeeded,
    _handle_subscription_deleted,
)
from src.db.models.donation import DonationStatus


class TestHandledEventTypesExtended:
    """Verify subscription event types are in the handled set."""

    def test_includes_invoice_payment_succeeded(self) -> None:
        assert EVENT_INVOICE_PAYMENT_SUCCEEDED in HANDLED_EVENT_TYPES

    def test_includes_invoice_payment_failed(self) -> None:
        assert EVENT_INVOICE_PAYMENT_FAILED in HANDLED_EVENT_TYPES

    def test_includes_subscription_deleted(self) -> None:
        assert EVENT_SUBSCRIPTION_DELETED in HANDLED_EVENT_TYPES


class TestHandleInvoicePaymentSucceeded:
    """Tests for _handle_invoice_payment_succeeded handler."""

    @pytest.mark.asyncio
    async def test_marks_pending_subscription_donation_completed(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.PENDING.value
        donation.amount_cents = 2000
        donation.currency = "EUR"
        donation.donor_id = uuid4()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        data_object = {"subscription": "sub_test123"}
        result = await _handle_invoice_payment_succeeded(db, data_object, None)

        assert result == "completed"
        assert donation.status == DonationStatus.COMPLETED.value
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_already_completed_for_renewal(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.COMPLETED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        data_object = {"subscription": "sub_test123"}
        result = await _handle_invoice_payment_succeeded(db, data_object, None)

        assert result == "already_completed"

    @pytest.mark.asyncio
    async def test_returns_not_subscription_when_no_subscription_id(self) -> None:
        db = AsyncMock()
        data_object = {"id": "in_test123"}
        result = await _handle_invoice_payment_succeeded(db, data_object, None)

        assert result == "not_subscription"
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_donation_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        data_object = {"subscription": "sub_unknown"}
        result = await _handle_invoice_payment_succeeded(db, data_object, None)

        assert result == "donation_not_found"

    @pytest.mark.asyncio
    async def test_publishes_domain_event_on_completion(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.PENDING.value
        donation.amount_cents = 2000
        donation.currency = "EUR"
        donation.donor_id = uuid4()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        event_bus = AsyncMock()
        event_bus.is_running = True

        data_object = {"subscription": "sub_test123"}
        result = await _handle_invoice_payment_succeeded(db, data_object, event_bus)

        assert result == "completed"
        event_bus.publish.assert_awaited_once()


class TestHandleInvoicePaymentFailed:
    """Tests for _handle_invoice_payment_failed handler."""

    @pytest.mark.asyncio
    async def test_marks_donation_failed(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.PENDING.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        data_object = {"subscription": "sub_test123"}
        result = await _handle_invoice_payment_failed(db, data_object)

        assert result == "failed"
        assert donation.status == DonationStatus.FAILED.value
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_already_failed(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.status = DonationStatus.FAILED.value

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        data_object = {"subscription": "sub_test123"}
        result = await _handle_invoice_payment_failed(db, data_object)

        assert result == "already_failed"

    @pytest.mark.asyncio
    async def test_returns_not_subscription(self) -> None:
        db = AsyncMock()
        data_object = {"id": "in_test123"}
        result = await _handle_invoice_payment_failed(db, data_object)

        assert result == "not_subscription"

    @pytest.mark.asyncio
    async def test_returns_donation_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        data_object = {"subscription": "sub_unknown"}
        result = await _handle_invoice_payment_failed(db, data_object)

        assert result == "donation_not_found"


class TestHandleSubscriptionDeleted:
    """Tests for _handle_subscription_deleted handler."""

    @pytest.mark.asyncio
    async def test_marks_donation_not_recurring(self) -> None:
        donation = MagicMock()
        donation.id = uuid4()
        donation.is_recurring = True

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = donation
        db.execute.return_value = mock_result

        data_object = {"id": "sub_test123"}
        result = await _handle_subscription_deleted(db, data_object)

        assert result == "cancelled"
        assert donation.is_recurring is False
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_donation_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        data_object = {"id": "sub_unknown"}
        result = await _handle_subscription_deleted(db, data_object)

        assert result == "donation_not_found"

    @pytest.mark.asyncio
    async def test_returns_no_subscription_id(self) -> None:
        db = AsyncMock()
        data_object = {"status": "canceled"}
        result = await _handle_subscription_deleted(db, data_object)

        assert result == "no_subscription_id"
