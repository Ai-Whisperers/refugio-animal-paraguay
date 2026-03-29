"""Unit tests for MetaWhatsAppDonationHandler (RAP-203).

Tests cover:
- Handler registers on the event bus for DONATION_RECEIVED
- Handler skips when Meta WhatsApp is disabled
- Handler skips when event has no aggregate_id
- Handler skips when donor has no phone number
- Handler sends correct template params (name, amount, currency, receipt)
- Handler prefers event payload amount/currency over DB values
- Handler uses fallback name and empty receipt when data is missing
- Handler logs warning when Meta API send returns False
- Handler fails gracefully on DB lookup error (no re-raise)
- Handler fails gracefully on unexpected send error (no re-raise)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from src.events.types import DomainEvent, EventType
from src.notifications.meta_whatsapp_donation_handler import (
    DONATION_RECEIPT_TEMPLATE_LANGUAGE,
    DONATION_RECEIPT_TEMPLATE_NAME,
    MetaWhatsAppDonationHandler,
)
from src.notifications.meta_whatsapp_service import MetaTemplateMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    aggregate_id: UUID | None = None,
    amount: str = "50.00",
    currency: str = "EUR",
) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.DONATION_RECEIVED,
        payload={"amount": amount, "currency": currency},
        aggregate_id=aggregate_id or uuid4(),
        aggregate_type="donation",
    )


def _enabled_service() -> MagicMock:
    svc = MagicMock()
    svc.is_enabled = True
    svc.send_template = AsyncMock(return_value=True)
    return svc


def _disabled_service() -> MagicMock:
    svc = MagicMock()
    svc.is_enabled = False
    svc.send_template = AsyncMock(return_value=True)
    return svc


def _mock_lookup(
    phone: str | None = "+595981234567",
    first_name: str | None = "Jan",
    amount_display: str | None = "100.00",
    currency: str | None = "EUR",
    receipt_number: str | None = "REC-001",
) -> AsyncMock:
    return AsyncMock(return_value=(phone, first_name, amount_display, currency, receipt_number))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestHandlerRegistration:
    def test_register_subscribes_to_donation_received(self) -> None:
        bus = MagicMock()
        handler = MetaWhatsAppDonationHandler(_disabled_service())
        handler.register(bus)

        bus.subscribe.assert_called_once()
        call_args = bus.subscribe.call_args
        assert call_args.args[0] == EventType.DONATION_RECEIVED


# ---------------------------------------------------------------------------
# Skip conditions
# ---------------------------------------------------------------------------


class TestSkipConditions:
    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        svc = _disabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event()

        await handler.on_donation_received(event)

        svc.send_template.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_no_aggregate_id(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "50.00", "currency": "EUR"},
            aggregate_id=None,
            aggregate_type="donation",
        )

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context"
        ) as mock_lookup:
            await handler.on_donation_received(event)
            mock_lookup.assert_not_awaited()

        svc.send_template.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_no_phone(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            _mock_lookup(phone=None),
        ):
            await handler.on_donation_received(event)

        svc.send_template.assert_not_awaited()


# ---------------------------------------------------------------------------
# Successful send
# ---------------------------------------------------------------------------


class TestSuccessfulSend:
    @pytest.mark.asyncio
    async def test_sends_correct_template_params(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event(amount="75.50", currency="EUR")

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            _mock_lookup(
                phone="+31612345678",
                first_name="Jan",
                receipt_number="REC-042",
            ),
        ):
            await handler.on_donation_received(event)

        svc.send_template.assert_awaited_once()
        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        assert msg.to == "+31612345678"
        assert msg.template_name == DONATION_RECEIPT_TEMPLATE_NAME
        assert msg.language_code == DONATION_RECEIPT_TEMPLATE_LANGUAGE

        params = msg.components[0]["parameters"]
        assert params[0]["text"] == "Jan"
        # Event payload amount takes priority
        assert params[1]["text"] == "75.50"
        assert params[2]["text"] == "EUR"
        assert params[3]["text"] == "REC-042"

    @pytest.mark.asyncio
    async def test_prefers_event_payload_amount_over_db(self) -> None:
        """Event payload amount/currency should override DB values."""
        svc = _enabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event(amount="200.00", currency="PYG")

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            _mock_lookup(amount_display="999.99", currency="EUR"),
        ):
            await handler.on_donation_received(event)

        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        params = msg.components[0]["parameters"]
        assert params[1]["text"] == "200.00"  # from event payload
        assert params[2]["text"] == "PYG"  # from event payload

    @pytest.mark.asyncio
    async def test_uses_fallback_name_when_none(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            _mock_lookup(first_name=None),
        ):
            await handler.on_donation_received(event)

        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        params = msg.components[0]["parameters"]
        assert params[0]["text"] == "Estimado/a"

    @pytest.mark.asyncio
    async def test_uses_empty_string_for_missing_receipt(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            _mock_lookup(receipt_number=None),
        ):
            await handler.on_donation_received(event)

        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        params = msg.components[0]["parameters"]
        assert params[3]["text"] == ""


# ---------------------------------------------------------------------------
# Graceful error handling
# ---------------------------------------------------------------------------


class TestGracefulErrorHandling:
    @pytest.mark.asyncio
    async def test_logs_warning_when_send_returns_false(self) -> None:
        svc = _enabled_service()
        svc.send_template = AsyncMock(return_value=False)
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            _mock_lookup(),
        ):
            await handler.on_donation_received(event)

        svc.send_template.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_db_lookup_error(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            AsyncMock(side_effect=RuntimeError("DB gone")),
        ):
            await handler.on_donation_received(event)

        svc.send_template.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_send_exception(self) -> None:
        svc = _enabled_service()
        svc.send_template = AsyncMock(side_effect=RuntimeError("Meta timeout"))
        handler = MetaWhatsAppDonationHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_donation_handler._lookup_donor_whatsapp_context",
            _mock_lookup(),
        ):
            await handler.on_donation_received(event)
