"""Unit tests for impact notification service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.events.domain_events import DonationAllocated, create_donation_allocated
from src.events.types import EventType
from src.services.impact_notification_service import (
    IMPACT_EMAIL_TEMPLATE,
    IMPACT_NOTIFICATION_TYPE,
    ImpactNotification,
    ImpactNotificationHandlers,
    _build_impact_notification,
    _format_amount,
)

# --- Test _format_amount ---


class TestFormatAmount:
    """Tests for _format_amount."""

    def test_eur_formatting(self) -> None:
        assert _format_amount(1050, "EUR") == "€10.50"

    def test_eur_zero_cents(self) -> None:
        assert _format_amount(2000, "EUR") == "€20.00"

    def test_usd_formatting(self) -> None:
        assert _format_amount(999, "USD") == "$9.99"

    def test_pyg_formatting(self) -> None:
        assert _format_amount(500000, "PYG") == "500,000 Gs."

    def test_pyg_small_amount(self) -> None:
        assert _format_amount(1000, "PYG") == "1,000 Gs."


# --- Test _build_impact_notification ---


class TestBuildImpactNotification:
    """Tests for _build_impact_notification."""

    def test_builds_notification_with_donor(self) -> None:
        donor_id = uuid4()
        donation_id = uuid4()
        expense_id = uuid4()
        event = create_donation_allocated(
            aggregate_id=donation_id,
            donation_id=donation_id,
            expense_id=expense_id,
            amount_cents=5000,
            currency="EUR",
            expense_description="Dog food purchase",
            donor_id=donor_id,
            donor_email="donor@example.com",
        )

        result = _build_impact_notification(event)

        assert result is not None
        assert result.donor_id == donor_id
        assert result.donor_email == "donor@example.com"
        assert result.donation_id == donation_id
        assert result.expense_description == "Dog food purchase"
        assert result.amount_cents == 5000
        assert result.currency == "EUR"

    def test_returns_none_for_anonymous_donation(self) -> None:
        event = create_donation_allocated(
            aggregate_id=uuid4(),
            donation_id=uuid4(),
            expense_id=uuid4(),
            amount_cents=1000,
            currency="PYG",
            expense_description="Medical supplies",
            donor_id=None,
            donor_email=None,
        )

        result = _build_impact_notification(event)
        assert result is None

    def test_builds_with_email_only(self) -> None:
        event = create_donation_allocated(
            aggregate_id=uuid4(),
            donation_id=uuid4(),
            expense_id=uuid4(),
            amount_cents=2000,
            currency="EUR",
            expense_description="Transport",
            donor_id=None,
            donor_email="anonymous@example.com",
        )

        result = _build_impact_notification(event)
        assert result is not None
        assert result.donor_id is None
        assert result.donor_email == "anonymous@example.com"


# --- Test ImpactNotificationHandlers ---


class TestImpactNotificationHandlers:
    """Tests for ImpactNotificationHandlers."""

    def test_register_subscribes_to_event(self) -> None:
        handlers = ImpactNotificationHandlers()
        bus = MagicMock()

        handlers.register(bus)

        bus.subscribe.assert_called_once_with(
            EventType.DONATION_ALLOCATED,
            handlers._handle_donation_allocated,
        )

    @pytest.mark.asyncio
    async def test_handles_allocation_event(self) -> None:
        handlers = ImpactNotificationHandlers()
        event = create_donation_allocated(
            aggregate_id=uuid4(),
            donation_id=uuid4(),
            expense_id=uuid4(),
            amount_cents=3000,
            currency="EUR",
            expense_description="Vaccination",
            donor_id=uuid4(),
            donor_email="test@example.com",
        )

        await handlers._handle_donation_allocated(event)

        assert len(handlers.notifications_sent) == 1
        assert handlers.notifications_sent[0].expense_description == "Vaccination"

    @pytest.mark.asyncio
    async def test_skips_anonymous_donation(self) -> None:
        handlers = ImpactNotificationHandlers()
        event = create_donation_allocated(
            aggregate_id=uuid4(),
            donation_id=uuid4(),
            expense_id=uuid4(),
            amount_cents=1000,
            currency="PYG",
            expense_description="Food",
            donor_id=None,
            donor_email=None,
        )

        await handlers._handle_donation_allocated(event)

        assert len(handlers.notifications_sent) == 0

    @pytest.mark.asyncio
    async def test_sends_email_when_service_configured(self) -> None:
        email_service = AsyncMock()
        email_service.send_template = AsyncMock()
        handlers = ImpactNotificationHandlers(email_service=email_service)

        event = create_donation_allocated(
            aggregate_id=uuid4(),
            donation_id=uuid4(),
            expense_id=uuid4(),
            amount_cents=5000,
            currency="EUR",
            expense_description="Surgery",
            donor_id=uuid4(),
            donor_email="donor@example.com",
        )

        await handlers._handle_donation_allocated(event)

        email_service.send_template.assert_awaited_once()
        call_kwargs = email_service.send_template.call_args[1]
        assert call_kwargs["to_email"] == "donor@example.com"
        assert call_kwargs["template_name"] == IMPACT_EMAIL_TEMPLATE

    @pytest.mark.asyncio
    async def test_email_failure_does_not_raise(self) -> None:
        email_service = AsyncMock()
        email_service.send_template = AsyncMock(side_effect=RuntimeError("SMTP down"))
        handlers = ImpactNotificationHandlers(email_service=email_service)

        event = create_donation_allocated(
            aggregate_id=uuid4(),
            donation_id=uuid4(),
            expense_id=uuid4(),
            amount_cents=1000,
            currency="EUR",
            expense_description="Food",
            donor_id=uuid4(),
            donor_email="donor@example.com",
        )

        # Should not raise even though email fails
        await handlers._handle_donation_allocated(event)

        assert len(handlers.notifications_sent) == 1

    @pytest.mark.asyncio
    async def test_no_email_when_no_service(self) -> None:
        handlers = ImpactNotificationHandlers(email_service=None)

        event = create_donation_allocated(
            aggregate_id=uuid4(),
            donation_id=uuid4(),
            expense_id=uuid4(),
            amount_cents=2000,
            currency="USD",
            expense_description="Shelter repair",
            donor_id=uuid4(),
            donor_email="donor@example.com",
        )

        await handlers._handle_donation_allocated(event)

        # Still recorded as sent, just no email
        assert len(handlers.notifications_sent) == 1


# --- Test DonationAllocated event ---


class TestDonationAllocatedEvent:
    """Tests for DonationAllocated domain event."""

    def test_event_type(self) -> None:
        event = DonationAllocated(
            payload={},
            aggregate_id=uuid4(),
        )
        assert event.event_type == EventType.DONATION_ALLOCATED
        assert event.aggregate_type == "donation"

    def test_factory_creates_correct_payload(self) -> None:
        donation_id = uuid4()
        expense_id = uuid4()
        donor_id = uuid4()

        event = create_donation_allocated(
            aggregate_id=donation_id,
            donation_id=donation_id,
            expense_id=expense_id,
            amount_cents=10000,
            currency="EUR",
            expense_description="Medical supplies",
            donor_id=donor_id,
            donor_email="test@example.com",
        )

        assert event.payload["donation_id"] == str(donation_id)
        assert event.payload["expense_id"] == str(expense_id)
        assert event.payload["amount_cents"] == 10000
        assert event.payload["currency"] == "EUR"
        assert event.payload["expense_description"] == "Medical supplies"
        assert event.payload["donor_id"] == str(donor_id)
        assert event.payload["donor_email"] == "test@example.com"


# --- Test dataclass ---


class TestImpactNotificationDataclass:
    """Tests for ImpactNotification dataclass."""

    def test_creates_notification(self) -> None:
        notif = ImpactNotification(
            donor_id=uuid4(),
            donor_email="test@example.com",
            donation_id=uuid4(),
            expense_description="Food",
            amount_cents=5000,
            currency="EUR",
            expense_id=uuid4(),
        )
        assert notif.donor_email == "test@example.com"
        assert notif.amount_cents == 5000


# --- Test constants ---


class TestConstants:
    """Tests for service constants."""

    def test_email_template_name(self) -> None:
        assert IMPACT_EMAIL_TEMPLATE == "donation_impact"

    def test_notification_type(self) -> None:
        assert IMPACT_NOTIFICATION_TYPE == "donation_impact"
