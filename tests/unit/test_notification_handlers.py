"""Unit tests for notification event handlers.

Tests cover:
  - Handler registration on event bus
  - Adoption request created handler (adopter + staff alerts)
  - Adoption status changed handler
  - Donation received handler
  - _lookup_adoption_context DB helper
  - _lookup_donation_context DB helper
  - _get_staff_emails DB helper
  - Error handling (missing aggregate_id, DB lookup failures)
"""

import asyncio
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.notifications.handlers import NotificationHandlers
from src.notifications.service import EmailService
from src.notifications.templates import TemplateRenderer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_handlers() -> tuple[NotificationHandlers, MagicMock, MagicMock]:
    """Create a NotificationHandlers with mocked email service and renderer."""
    email_service = MagicMock(spec=EmailService)
    email_service.send_email = AsyncMock(return_value=True)
    renderer = MagicMock(spec=TemplateRenderer)
    renderer.render.return_value = "<html>test</html>"
    handlers = NotificationHandlers(email_service, renderer)
    return handlers, email_service, renderer


def _make_adoption_event(
    aggregate_id: UUID | None = None,
    old_status: str = "pending",
    new_status: str = "approved",
) -> DomainEvent:
    """Create an adoption status changed event."""
    return DomainEvent(
        event_type=EventType.ADOPTION_STATUS_CHANGED,
        payload={"old_status": old_status, "new_status": new_status},
        aggregate_id=aggregate_id or uuid4(),
    )


def _make_donation_event(
    aggregate_id: UUID | None = None,
    amount: str = "50.00",
    currency: str = "EUR",
) -> DomainEvent:
    """Create a donation received event."""
    return DomainEvent(
        event_type=EventType.DONATION_RECEIVED,
        payload={"amount": amount, "currency": currency},
        aggregate_id=aggregate_id or uuid4(),
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestHandlerRegistration:
    """Verify handlers are registered on the event bus."""

    def test_register_subscribes_adoption_handler(self) -> None:
        handlers, _, _ = _make_handlers()
        bus = EventBus()
        handlers.register(bus)
        adoption_handlers = bus.get_handlers(EventType.ADOPTION_STATUS_CHANGED)
        assert len(adoption_handlers) == 1

    def test_register_subscribes_donation_handler(self) -> None:
        handlers, _, _ = _make_handlers()
        bus = EventBus()
        handlers.register(bus)
        donation_handlers = bus.get_handlers(EventType.DONATION_RECEIVED)
        assert len(donation_handlers) == 1


# ---------------------------------------------------------------------------
# Adoption Status Changed Handler
# ---------------------------------------------------------------------------
class TestAdoptionStatusChangedHandler:
    """Test on_adoption_status_changed handler."""

    @pytest.mark.asyncio
    async def test_sends_email_on_valid_event(self) -> None:
        handlers, email_service, _renderer = _make_handlers()
        event = _make_adoption_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=("adopter@test.com", "Maria Garcia", "Luna"),
        ):
            await handlers.on_adoption_status_changed(event)

        email_service.send_email.assert_called_once()
        call_args = email_service.send_email.call_args[0][0]
        assert call_args.to == "adopter@test.com"
        assert "Approved" in call_args.subject

    @pytest.mark.asyncio
    async def test_renders_correct_template(self) -> None:
        handlers, _, renderer = _make_handlers()
        event = _make_adoption_event(old_status="pending", new_status="rejected")

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=("adopter@test.com", "Maria", "Luna"),
        ):
            await handlers.on_adoption_status_changed(event)

        renderer.render.assert_called_once_with(
            "adoption_status_changed",
            {
                "adopter_name": "Maria",
                "animal_name": "Luna",
                "old_status": "pending",
                "new_status": "rejected",
                "staff_notes": None,
            },
        )

    @pytest.mark.asyncio
    async def test_skips_when_no_aggregate_id(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = DomainEvent(
            event_type=EventType.ADOPTION_STATUS_CHANGED,
            payload={"old_status": "pending", "new_status": "approved"},
            aggregate_id=None,
        )
        await handlers.on_adoption_status_changed(event)
        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_adopter_email_not_found(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_adoption_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=(None, None, None),
        ):
            await handlers.on_adoption_status_changed(event)

        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers, _, _ = _make_handlers()
        event = _make_adoption_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB exploded"),
        ):
            # Should not raise
            await handlers.on_adoption_status_changed(event)


# ---------------------------------------------------------------------------
# Donation Received Handler
# ---------------------------------------------------------------------------
class TestDonationReceivedHandler:
    """Test on_donation_received handler."""

    @pytest.mark.asyncio
    async def test_sends_email_on_valid_event(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_donation_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_donation_context",
            new_callable=AsyncMock,
            return_value=("donor@test.com", "Jan de Vries", "50.00", "EUR", "RCP-001"),
        ):
            await handlers.on_donation_received(event)

        email_service.send_email.assert_called_once()
        call_args = email_service.send_email.call_args[0][0]
        assert call_args.to == "donor@test.com"
        assert "Donation" in call_args.subject

    @pytest.mark.asyncio
    async def test_skips_when_no_aggregate_id(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = DomainEvent(
            event_type=EventType.DONATION_RECEIVED,
            payload={"amount": "50.00", "currency": "EUR"},
            aggregate_id=None,
        )
        await handlers.on_donation_received(event)
        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_donor_email_not_found(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_donation_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_donation_context",
            new_callable=AsyncMock,
            return_value=(None, None, None, None, None),
        ):
            await handlers.on_donation_received(event)

        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers, _, _ = _make_handlers()
        event = _make_donation_event()

        with patch.object(
            NotificationHandlers,
            "_lookup_donation_context",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB exploded"),
        ):
            await handlers.on_donation_received(event)


# ---------------------------------------------------------------------------
# End-to-End with EventBus (unit level)
# ---------------------------------------------------------------------------
class TestHandlersWithEventBus:
    """Verify handlers fire when events are published through the bus."""

    @pytest.mark.asyncio
    async def test_adoption_event_triggers_handler_via_bus(self) -> None:
        handlers, email_service, _ = _make_handlers()
        bus = EventBus()
        handlers.register(bus)
        await bus.start()

        event = _make_adoption_event()
        with patch.object(
            NotificationHandlers,
            "_lookup_adoption_context",
            new_callable=AsyncMock,
            return_value=("adopter@test.com", "Maria", "Luna"),
        ):
            await bus.publish(event)
            await asyncio.sleep(0.2)

        await bus.stop()
        email_service.send_email.assert_called_once()


# ---------------------------------------------------------------------------
# Adoption Request Created Handler
# ---------------------------------------------------------------------------


def _make_adoption_request_created_event(
    adopter_email: str | None = "applicant@example.com",
    adopter_name: str = "Maria Garcia",
    animal_name: str = "Luna",
) -> DomainEvent:
    payload: dict = {"adopter_name": adopter_name, "animal_name": animal_name}
    if adopter_email is not None:
        payload["adopter_email"] = adopter_email
    return DomainEvent(
        event_type=EventType.ADOPTION_REQUEST_CREATED,
        payload=payload,
        aggregate_id=uuid4(),
    )


class TestAdoptionRequestCreatedHandler:
    """Test on_adoption_request_created handler."""

    @pytest.mark.asyncio
    async def test_sends_adopter_confirmation_email(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_adoption_request_created_event()

        with patch.object(
            NotificationHandlers,
            "_get_staff_emails",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await handlers.on_adoption_request_created(event)

        email_service.send_email.assert_called_once()
        call_args = email_service.send_email.call_args[0][0]
        assert call_args.to == "applicant@example.com"
        assert "Adoption" in call_args.subject

    @pytest.mark.asyncio
    async def test_sends_staff_alert_emails(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_adoption_request_created_event()
        staff_emails = ["staff1@shelter.org", "staff2@shelter.org"]

        with patch.object(
            NotificationHandlers,
            "_get_staff_emails",
            new_callable=AsyncMock,
            return_value=staff_emails,
        ):
            await handlers.on_adoption_request_created(event)

        # 1 adopter email + 2 staff emails = 3 calls
        assert email_service.send_email.call_count == 3
        all_recipients = [c[0][0].to for c in email_service.send_email.call_args_list]
        assert "staff1@shelter.org" in all_recipients
        assert "staff2@shelter.org" in all_recipients

    @pytest.mark.asyncio
    async def test_skips_adopter_email_when_none_in_payload(self) -> None:
        handlers, email_service, _ = _make_handlers()
        event = _make_adoption_request_created_event(adopter_email=None)

        with patch.object(
            NotificationHandlers,
            "_get_staff_emails",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await handlers.on_adoption_request_created(event)

        email_service.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers, _, _ = _make_handlers()
        event = _make_adoption_request_created_event()

        with patch.object(
            NotificationHandlers,
            "_get_staff_emails",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB exploded"),
        ):
            await handlers.on_adoption_request_created(event)


# ---------------------------------------------------------------------------
# _lookup_adoption_context
# ---------------------------------------------------------------------------


def _make_fake_session() -> MagicMock:
    """Build a minimal async DB session double."""
    session = MagicMock()
    session.execute = AsyncMock()
    return session


def _patch_handlers_session(session: MagicMock):
    """Patch get_async_session used inside handlers.py."""

    @asynccontextmanager
    async def _fake():
        yield session

    return patch("src.notifications.handlers.get_async_session", _fake)


class TestLookupAdoptionContext:
    """Test NotificationHandlers._lookup_adoption_context static method."""

    @pytest.mark.asyncio
    async def test_returns_none_tuple_when_request_not_found(self) -> None:
        session = _make_fake_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        with _patch_handlers_session(session):
            email, name, animal = await NotificationHandlers._lookup_adoption_context(uuid4())

        assert email is None
        assert name is None
        assert animal is None

    @pytest.mark.asyncio
    async def test_returns_adopter_and_animal_data(self) -> None:
        session = _make_fake_session()

        adoption_request = MagicMock()
        adoption_request.adopter_id = uuid4()
        adoption_request.animal_id = uuid4()

        adopter = MagicMock()
        adopter.email = "adopter@example.com"
        adopter.full_name = "Maria Garcia"

        animal = MagicMock()
        animal.name = "Luna"

        # execute() is called 3 times: request, adopter, animal
        result_request = MagicMock()
        result_request.scalar_one_or_none.return_value = adoption_request
        result_adopter = MagicMock()
        result_adopter.scalar_one_or_none.return_value = adopter
        result_animal = MagicMock()
        result_animal.scalar_one_or_none.return_value = animal

        session.execute = AsyncMock(side_effect=[result_request, result_adopter, result_animal])

        with _patch_handlers_session(session):
            email, name, animal_name = await NotificationHandlers._lookup_adoption_context(uuid4())

        assert email == "adopter@example.com"
        assert name == "Maria Garcia"
        assert animal_name == "Luna"

    @pytest.mark.asyncio
    async def test_returns_none_tuple_on_db_exception(self) -> None:
        session = _make_fake_session()
        session.execute = AsyncMock(side_effect=RuntimeError("DB error"))

        with _patch_handlers_session(session):
            result = await NotificationHandlers._lookup_adoption_context(uuid4())

        assert result == (None, None, None)


# ---------------------------------------------------------------------------
# _lookup_donation_context
# ---------------------------------------------------------------------------


class TestLookupDonationContext:
    """Test NotificationHandlers._lookup_donation_context static method."""

    @pytest.mark.asyncio
    async def test_returns_none_tuple_when_donation_not_found(self) -> None:
        session = _make_fake_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute.return_value = result_mock

        with _patch_handlers_session(session):
            result = await NotificationHandlers._lookup_donation_context(uuid4())

        assert result == (None, None, None, None, None)

    @pytest.mark.asyncio
    async def test_returns_donor_and_donation_data(self) -> None:
        session = _make_fake_session()

        donation = MagicMock()
        donation.donor_id = uuid4()
        donation.amount_cents = 5000
        donation.currency = "EUR"

        donor = MagicMock()
        donor.email = "donor@example.com"
        donor.full_name = "Jan de Vries"

        result_donation = MagicMock()
        result_donation.scalar_one_or_none.return_value = donation
        result_donor = MagicMock()
        result_donor.scalar_one_or_none.return_value = donor

        session.execute = AsyncMock(side_effect=[result_donation, result_donor])

        with _patch_handlers_session(session):
            email, name, amount, currency, _ = await NotificationHandlers._lookup_donation_context(
                uuid4()
            )

        assert email == "donor@example.com"
        assert name == "Jan de Vries"
        assert amount == "50.00"
        assert currency == "EUR"

    @pytest.mark.asyncio
    async def test_returns_none_tuple_on_db_exception(self) -> None:
        session = _make_fake_session()
        session.execute = AsyncMock(side_effect=RuntimeError("DB error"))

        with _patch_handlers_session(session):
            result = await NotificationHandlers._lookup_donation_context(uuid4())

        assert result == (None, None, None, None, None)


# ---------------------------------------------------------------------------
# _get_staff_emails
# ---------------------------------------------------------------------------


class TestGetStaffEmails:
    """Test NotificationHandlers._get_staff_emails static method."""

    @pytest.mark.asyncio
    async def test_returns_staff_email_list(self) -> None:
        session = _make_fake_session()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = ["staff@shelter.org", "admin@shelter.org"]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        session.execute.return_value = result_mock

        with _patch_handlers_session(session):
            emails = await NotificationHandlers._get_staff_emails()

        assert emails == ["staff@shelter.org", "admin@shelter.org"]

    @pytest.mark.asyncio
    async def test_filters_out_none_emails(self) -> None:
        session = _make_fake_session()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = ["staff@shelter.org", None, "admin@shelter.org"]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        session.execute.return_value = result_mock

        with _patch_handlers_session(session):
            emails = await NotificationHandlers._get_staff_emails()

        assert None not in emails
        assert len(emails) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_db_exception(self) -> None:
        session = _make_fake_session()
        session.execute = AsyncMock(side_effect=RuntimeError("DB error"))

        with _patch_handlers_session(session):
            emails = await NotificationHandlers._get_staff_emails()

        assert emails == []
