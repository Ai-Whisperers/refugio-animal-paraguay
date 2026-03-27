"""Unit tests for InAppNotificationHandlers.

Tests cover:
  - Handler registration on event bus
  - All four domain event handlers (adoption created/changed, donation, intake)
  - Exception isolation — handlers log errors but never raise
  - _notify_all_staff DB interaction (mocked via get_async_session)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from src.events.bus import EventBus
from src.events.types import DomainEvent, EventType
from src.notifications.in_app_handlers import InAppNotificationHandlers

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handlers() -> InAppNotificationHandlers:
    return InAppNotificationHandlers()


def _event(event_type: EventType, payload: dict | None = None) -> DomainEvent:
    return DomainEvent(
        event_type=event_type,
        payload=payload or {},
        aggregate_id=uuid4(),
    )


def _make_fake_session(user_ids: list[UUID]) -> MagicMock:
    """Build a minimal async session double that returns the given user IDs."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = user_ids
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    session = MagicMock()
    session.execute = AsyncMock(return_value=result_mock)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _patch_db(user_ids: list[UUID]):
    """Patch get_async_session to return a fake session yielding user_ids."""
    fake_session = _make_fake_session(user_ids)

    @asynccontextmanager
    async def _fake_get_async_session():
        yield fake_session

    return patch(
        "src.notifications.in_app_handlers.get_async_session",
        _fake_get_async_session,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestHandlerRegistration:

    def test_register_subscribes_four_handlers(self) -> None:
        bus = EventBus()
        handlers = _make_handlers()
        handlers.register(bus)

        assert len(bus.get_handlers(EventType.ADOPTION_REQUEST_CREATED)) == 1
        assert len(bus.get_handlers(EventType.ADOPTION_STATUS_CHANGED)) == 1
        assert len(bus.get_handlers(EventType.DONATION_RECEIVED)) == 1
        assert len(bus.get_handlers(EventType.ANIMAL_INTAKE_COMPLETED)) == 1


# ---------------------------------------------------------------------------
# on_adoption_request_created
# ---------------------------------------------------------------------------


class TestOnAdoptionRequestCreated:

    @pytest.mark.asyncio
    async def test_notifies_staff_on_valid_event(self) -> None:
        handlers = _make_handlers()
        event = _event(
            EventType.ADOPTION_REQUEST_CREATED,
            {"adopter_name": "Maria Garcia", "animal_name": "Luna"},
        )
        user_ids = [uuid4(), uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_adoption_request_created(event)

        assert mock_create.await_count == len(user_ids)

    @pytest.mark.asyncio
    async def test_uses_defaults_when_payload_empty(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_REQUEST_CREATED, {})
        user_ids = [uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_adoption_request_created(event)

        # Defaults used: "Unknown adopter" and "an animal"
        call_kwargs = mock_create.call_args
        assert "Unknown adopter" in str(call_kwargs)
        mock_create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_REQUEST_CREATED)

        with patch(
            "src.notifications.in_app_handlers.get_async_session",
            side_effect=RuntimeError("DB down"),
        ):
            # Must not propagate — handler isolates failures
            await handlers.on_adoption_request_created(event)

    @pytest.mark.asyncio
    async def test_skips_create_when_no_staff(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_REQUEST_CREATED)
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_adoption_request_created(event)

        mock_create.assert_not_awaited()


# ---------------------------------------------------------------------------
# on_adoption_status_changed
# ---------------------------------------------------------------------------


class TestOnAdoptionStatusChanged:

    @pytest.mark.asyncio
    async def test_notifies_staff_with_status_info(self) -> None:
        handlers = _make_handlers()
        event = _event(
            EventType.ADOPTION_STATUS_CHANGED,
            {"old_status": "pending", "new_status": "approved"},
        )
        user_id = uuid4()
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([user_id]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_adoption_status_changed(event)

        mock_create.assert_awaited_once()
        call_str = str(mock_create.call_args)
        assert "pending" in call_str
        assert "approved" in call_str

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_STATUS_CHANGED)

        with patch(
            "src.notifications.in_app_handlers.get_async_session",
            side_effect=ConnectionError("DB timeout"),
        ):
            await handlers.on_adoption_status_changed(event)

    @pytest.mark.asyncio
    async def test_uses_unknown_defaults_on_empty_payload(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_STATUS_CHANGED, {})
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([uuid4()]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_adoption_status_changed(event)

        mock_create.assert_awaited_once()
        call_str = str(mock_create.call_args)
        assert "unknown" in call_str


# ---------------------------------------------------------------------------
# on_donation_received
# ---------------------------------------------------------------------------


class TestOnDonationReceived:

    @pytest.mark.asyncio
    async def test_notifies_staff_on_donation(self) -> None:
        handlers = _make_handlers()
        event = _event(
            EventType.DONATION_RECEIVED,
            {"amount": "100.00", "currency": "EUR", "donor_name": "Jan de Vries"},
        )
        user_id = uuid4()
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([user_id]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_donation_received(event)

        mock_create.assert_awaited_once()
        call_str = str(mock_create.call_args)
        assert "Jan de Vries" in call_str
        assert "100.00" in call_str

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.DONATION_RECEIVED)

        with patch(
            "src.notifications.in_app_handlers.get_async_session",
            side_effect=OSError("socket closed"),
        ):
            await handlers.on_donation_received(event)

    @pytest.mark.asyncio
    async def test_uses_anonymous_default_donor_name(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.DONATION_RECEIVED, {"amount": "50", "currency": "PYG"})
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([uuid4()]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_donation_received(event)

        mock_create.assert_awaited_once()
        assert "Anonymous" in str(mock_create.call_args)


# ---------------------------------------------------------------------------
# on_animal_intake_completed
# ---------------------------------------------------------------------------


class TestOnAnimalIntakeCompleted:

    @pytest.mark.asyncio
    async def test_notifies_staff_on_intake(self) -> None:
        handlers = _make_handlers()
        event = _event(
            EventType.ANIMAL_INTAKE_COMPLETED,
            {"animal_name": "Rex", "species": "dog"},
        )
        user_id = uuid4()
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([user_id]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_animal_intake_completed(event)

        mock_create.assert_awaited_once()
        call_str = str(mock_create.call_args)
        assert "Rex" in call_str

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ANIMAL_INTAKE_COMPLETED)

        with patch(
            "src.notifications.in_app_handlers.get_async_session",
            side_effect=RuntimeError("queue full"),
        ):
            await handlers.on_animal_intake_completed(event)

    @pytest.mark.asyncio
    async def test_uses_default_animal_name_when_missing(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ANIMAL_INTAKE_COMPLETED, {})
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([uuid4()]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_animal_intake_completed(event)

        mock_create.assert_awaited_once()
        assert "New animal" in str(mock_create.call_args)


# ---------------------------------------------------------------------------
# _notify_all_staff: DB interaction
# ---------------------------------------------------------------------------


class TestNotifyAllStaff:

    @pytest.mark.asyncio
    async def test_calls_create_notification_per_staff_user(self) -> None:
        handlers = _make_handlers()
        user_ids = [uuid4(), uuid4(), uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers._notify_all_staff(
                notification_type="test.type",
                title="Test",
                message="Test message",
                data={"key": "value"},
            )

        assert mock_create.await_count == 3

    @pytest.mark.asyncio
    async def test_does_nothing_when_no_staff_users(self) -> None:
        handlers = _make_handlers()
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers._notify_all_staff(
                notification_type="test.type",
                title="Test",
                message="No staff",
            )

        mock_create.assert_not_awaited()
