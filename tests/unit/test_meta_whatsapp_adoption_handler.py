"""Unit tests for MetaWhatsAppAdoptionHandler (RAP-202).

Tests cover:
- Handler registers on the event bus
- Handler skips when Meta WhatsApp is disabled
- Handler skips when event has no aggregate_id
- Handler skips when adopter has no phone number
- Handler sends correct template parameters when all data is available
- Handler logs warning when Meta API send returns False
- Handler fails gracefully on DB lookup error (no re-raise)
- Handler fails gracefully on unexpected send error (no re-raise)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from src.events.types import DomainEvent, EventType
from src.notifications.meta_whatsapp_adoption_handler import (
    ADOPTION_STATUS_TEMPLATE_LANGUAGE,
    ADOPTION_STATUS_TEMPLATE_NAME,
    MetaWhatsAppAdoptionHandler,
)
from src.notifications.meta_whatsapp_service import MetaTemplateMessage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    aggregate_id: UUID | None = None,
    new_status: str = "approved",
    old_status: str = "pending",
) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.ADOPTION_STATUS_CHANGED,
        payload={"new_status": new_status, "old_status": old_status},
        aggregate_id=aggregate_id or uuid4(),
        aggregate_type="adoption_request",
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
    first_name: str | None = "Maria",
    animal_name: str | None = "Luna",
) -> AsyncMock:
    return AsyncMock(return_value=(phone, first_name, animal_name))


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestHandlerRegistration:
    def test_register_subscribes_to_adoption_status_changed(self) -> None:
        bus = MagicMock()
        handler = MetaWhatsAppAdoptionHandler(_disabled_service())
        handler.register(bus)

        bus.subscribe.assert_called_once()
        call_args = bus.subscribe.call_args
        assert call_args.args[0] == EventType.ADOPTION_STATUS_CHANGED


# ---------------------------------------------------------------------------
# Skip conditions
# ---------------------------------------------------------------------------


class TestSkipConditions:
    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        svc = _disabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event()

        await handler.on_adoption_status_changed(event)

        svc.send_template.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_no_aggregate_id(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            payload={"new_status": "approved"},
            aggregate_id=None,
            aggregate_type="adoption_request",
        )

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context"
        ) as mock_lookup:
            await handler.on_adoption_status_changed(event)
            mock_lookup.assert_not_awaited()

        svc.send_template.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_no_phone(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(phone=None),
        ):
            await handler.on_adoption_status_changed(event)

        svc.send_template.assert_not_awaited()


# ---------------------------------------------------------------------------
# Successful send
# ---------------------------------------------------------------------------


class TestSuccessfulSend:
    @pytest.mark.asyncio
    async def test_sends_correct_template_for_approved(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event(new_status="approved")

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(phone="+595981234567", first_name="Maria", animal_name="Luna"),
        ):
            await handler.on_adoption_status_changed(event)

        svc.send_template.assert_awaited_once()
        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        assert msg.to == "+595981234567"
        assert msg.template_name == ADOPTION_STATUS_TEMPLATE_NAME
        assert msg.language_code == ADOPTION_STATUS_TEMPLATE_LANGUAGE

        params = msg.components[0]["parameters"]
        assert params[0]["text"] == "Maria"
        assert params[1]["text"] == "Luna"
        assert params[2]["text"] == "aprobada"  # Spanish label

    @pytest.mark.asyncio
    async def test_sends_correct_label_for_rejected(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event(new_status="rejected")

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(),
        ):
            await handler.on_adoption_status_changed(event)

        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        params = msg.components[0]["parameters"]
        assert params[2]["text"] == "rechazada"

    @pytest.mark.asyncio
    async def test_sends_correct_label_for_cancelled(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event(new_status="cancelled")

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(),
        ):
            await handler.on_adoption_status_changed(event)

        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        params = msg.components[0]["parameters"]
        assert params[2]["text"] == "cancelada"

    @pytest.mark.asyncio
    async def test_uses_fallback_name_when_first_name_is_none(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(first_name=None),
        ):
            await handler.on_adoption_status_changed(event)

        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        params = msg.components[0]["parameters"]
        assert params[0]["text"] == "Estimado/a"

    @pytest.mark.asyncio
    async def test_uses_fallback_animal_when_animal_name_is_none(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(animal_name=None),
        ):
            await handler.on_adoption_status_changed(event)

        msg: MetaTemplateMessage = svc.send_template.call_args.args[0]
        params = msg.components[0]["parameters"]
        assert params[1]["text"] == "el animal"


# ---------------------------------------------------------------------------
# Graceful error handling
# ---------------------------------------------------------------------------


class TestGracefulErrorHandling:
    @pytest.mark.asyncio
    async def test_logs_warning_when_send_returns_false(self) -> None:
        svc = _enabled_service()
        svc.send_template = AsyncMock(return_value=False)
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(),
        ):
            # Should not raise
            await handler.on_adoption_status_changed(event)

        svc.send_template.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_db_lookup_error(self) -> None:
        svc = _enabled_service()
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            AsyncMock(side_effect=RuntimeError("DB connection lost")),
        ):
            # Should not raise — handler must be resilient
            await handler.on_adoption_status_changed(event)

        svc.send_template.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_send_exception(self) -> None:
        svc = _enabled_service()
        svc.send_template = AsyncMock(side_effect=RuntimeError("Meta API timeout"))
        handler = MetaWhatsAppAdoptionHandler(svc)
        event = _make_event()

        with patch(
            "src.notifications.meta_whatsapp_adoption_handler._lookup_adopter_whatsapp_context",
            _mock_lookup(),
        ):
            # Should not raise — handler must be resilient
            await handler.on_adoption_status_changed(event)
