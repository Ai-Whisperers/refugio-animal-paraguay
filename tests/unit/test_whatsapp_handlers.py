"""Unit tests for WhatsApp event handlers.

Tests cover:
- Handlers register on the event bus
- Handlers skip dispatch when WhatsApp service is disabled
- Handlers skip dispatch when no phone number in payload
- Handlers call send_message with correct body for each event type
- Handlers log and continue on send_message failure
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.events.types import DomainEvent, EventType
from src.notifications.whatsapp_handlers import (
    TEMPLATE_ADOPTION_STATUS_UPDATE,
    TEMPLATE_SHIFT_CONFIRMATION,
    WhatsAppHandlers,
)
from src.notifications.whatsapp_service import WhatsAppMessage


def _make_event(event_type: EventType, payload: dict) -> DomainEvent:
    return DomainEvent(
        event_type=event_type,
        payload=payload,
        aggregate_id=uuid4(),
        aggregate_type="test",
    )


def _disabled_service() -> MagicMock:
    svc = MagicMock()
    svc.is_enabled = False
    svc.send_message = AsyncMock(return_value=True)
    return svc


def _enabled_service() -> MagicMock:
    svc = MagicMock()
    svc.is_enabled = True
    svc.send_message = AsyncMock(return_value=True)
    return svc


class TestHandlerRegistration:
    def test_register_subscribes_handlers(self) -> None:
        bus = MagicMock()
        handlers = WhatsAppHandlers(_disabled_service())
        handlers.register(bus)

        # Three subscriptions expected
        assert bus.subscribe.call_count == 3

        subscribed_events = {call.args[0] for call in bus.subscribe.call_args_list}
        assert EventType.ADOPTION_STATUS_CHANGED in subscribed_events
        assert EventType.VOLUNTEER_SHIFT_CREATED in subscribed_events
        assert EventType.VOLUNTEER_SHIFT_COMPLETED in subscribed_events


class TestAdoptionStatusChangedHandler:
    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        svc = _disabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.ADOPTION_STATUS_CHANGED,
            {"adopter_phone": "+595981234567"},
        )
        await handlers.on_adoption_status_changed(event)
        svc.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_no_phone(self) -> None:
        svc = _enabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(EventType.ADOPTION_STATUS_CHANGED, {})
        await handlers.on_adoption_status_changed(event)
        svc.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_sends_with_correct_body(self) -> None:
        svc = _enabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.ADOPTION_STATUS_CHANGED,
            {
                "adopter_phone": "+595981234567",
                "adopter_name": "Maria",
                "animal_name": "Toby",
                "old_status": "pendiente",
                "new_status": "aprobado",
            },
        )
        await handlers.on_adoption_status_changed(event)

        expected_body = TEMPLATE_ADOPTION_STATUS_UPDATE.format(
            adopter_name="Maria",
            animal_name="Toby",
            old_status="pendiente",
            new_status="aprobado",
        )
        svc.send_message.assert_awaited_once_with(
            WhatsAppMessage(to="+595981234567", body=expected_body)
        )

    @pytest.mark.asyncio
    async def test_logs_and_continues_on_exception(self) -> None:
        svc = _enabled_service()
        svc.send_message = AsyncMock(side_effect=Exception("Twilio error"))
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.ADOPTION_STATUS_CHANGED,
            {"adopter_phone": "+595981234567"},
        )
        # Should not raise
        await handlers.on_adoption_status_changed(event)


class TestVolunteerShiftCreatedHandler:
    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        svc = _disabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.VOLUNTEER_SHIFT_CREATED,
            {"volunteer_phone": "+595981234567"},
        )
        await handlers.on_volunteer_shift_created(event)
        svc.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_no_phone(self) -> None:
        svc = _enabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(EventType.VOLUNTEER_SHIFT_CREATED, {})
        await handlers.on_volunteer_shift_created(event)
        svc.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_sends_confirmation_body(self) -> None:
        svc = _enabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.VOLUNTEER_SHIFT_CREATED,
            {
                "volunteer_phone": "+595981234567",
                "volunteer_name": "Carlos",
                "shift_date": "27 de marzo",
                "shift_time": "09:00",
            },
        )
        await handlers.on_volunteer_shift_created(event)

        expected_body = TEMPLATE_SHIFT_CONFIRMATION.format(
            volunteer_name="Carlos",
            shift_date="27 de marzo",
            shift_time="09:00",
        )
        svc.send_message.assert_awaited_once_with(
            WhatsAppMessage(to="+595981234567", body=expected_body)
        )

    @pytest.mark.asyncio
    async def test_logs_and_continues_on_exception(self) -> None:
        svc = _enabled_service()
        svc.send_message = AsyncMock(side_effect=Exception("Connection refused"))
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.VOLUNTEER_SHIFT_CREATED,
            {"volunteer_phone": "+595981234567"},
        )
        await handlers.on_volunteer_shift_created(event)


class TestVolunteerShiftCompletedHandler:
    @pytest.mark.asyncio
    async def test_skips_when_disabled(self) -> None:
        svc = _disabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.VOLUNTEER_SHIFT_COMPLETED,
            {"volunteer_phone": "+595981234567"},
        )
        await handlers.on_volunteer_shift_completed(event)
        svc.send_message.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_sends_reminder_body(self) -> None:
        svc = _enabled_service()
        handlers = WhatsAppHandlers(svc)
        event = _make_event(
            EventType.VOLUNTEER_SHIFT_COMPLETED,
            {
                "volunteer_phone": "+595981234567",
                "shift_date": "mañana",
                "shift_time": "08:00",
            },
        )
        await handlers.on_volunteer_shift_completed(event)

        svc.send_message.assert_awaited_once()
        msg: WhatsAppMessage = svc.send_message.call_args.args[0]
        assert msg.to == "+595981234567"
        assert "mañana" in msg.body
        assert "08:00" in msg.body
