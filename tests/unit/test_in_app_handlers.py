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

        assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_uses_default_names_when_payload_missing(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_REQUEST_CREATED, {})
        user_ids = [uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_adoption_request_created(event)

        call_kwargs = mock_create.call_args[1]
        assert "Unknown adopter" in call_kwargs["message"]
        assert "an animal" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_REQUEST_CREATED, {"adopter_name": "Maria"})

        with (
            patch(
                "src.notifications.in_app_handlers.create_notification",
                side_effect=RuntimeError("DB exploded"),
            ),
            _patch_db([uuid4()]),
        ):
            await handlers.on_adoption_request_created(event)


# ---------------------------------------------------------------------------
# on_adoption_status_changed
# ---------------------------------------------------------------------------


class TestOnAdoptionStatusChanged:

    @pytest.mark.asyncio
    async def test_notifies_staff_with_status_transition(self) -> None:
        handlers = _make_handlers()
        event = _event(
            EventType.ADOPTION_STATUS_CHANGED,
            {"old_status": "pending", "new_status": "approved"},
        )
        user_ids = [uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_adoption_status_changed(event)

        assert mock_create.call_count == 1
        call_kwargs = mock_create.call_args[1]
        assert "pending" in call_kwargs["message"]
        assert "approved" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ADOPTION_STATUS_CHANGED, {})

        with (
            patch(
                "src.notifications.in_app_handlers.create_notification",
                side_effect=RuntimeError("DB exploded"),
            ),
            _patch_db([uuid4()]),
        ):
            await handlers.on_adoption_status_changed(event)


# ---------------------------------------------------------------------------
# on_donation_received
# ---------------------------------------------------------------------------


class TestOnDonationReceived:

    @pytest.mark.asyncio
    async def test_notifies_staff_with_donation_details(self) -> None:
        handlers = _make_handlers()
        event = _event(
            EventType.DONATION_RECEIVED,
            {"amount": "150.00", "currency": "EUR", "donor_name": "Jan de Vries"},
        )
        user_ids = [uuid4(), uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_donation_received(event)

        assert mock_create.call_count == 2
        call_kwargs = mock_create.call_args[1]
        assert "Jan de Vries" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.DONATION_RECEIVED, {})

        with (
            patch(
                "src.notifications.in_app_handlers.create_notification",
                side_effect=RuntimeError("DB exploded"),
            ),
            _patch_db([uuid4()]),
        ):
            await handlers.on_donation_received(event)


# ---------------------------------------------------------------------------
# on_animal_intake_completed
# ---------------------------------------------------------------------------


class TestOnAnimalIntakeCompleted:

    @pytest.mark.asyncio
    async def test_notifies_staff_with_animal_details(self) -> None:
        handlers = _make_handlers()
        event = _event(
            EventType.ANIMAL_INTAKE_COMPLETED,
            {"animal_name": "Firulais", "species": "dog"},
        )
        user_ids = [uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers.on_animal_intake_completed(event)

        assert mock_create.call_count == 1
        call_kwargs = mock_create.call_args[1]
        assert "Firulais" in call_kwargs["message"]
        assert "dog" in call_kwargs["message"]

    @pytest.mark.asyncio
    async def test_does_not_raise_on_exception(self) -> None:
        handlers = _make_handlers()
        event = _event(EventType.ANIMAL_INTAKE_COMPLETED, {})

        with (
            patch(
                "src.notifications.in_app_handlers.create_notification",
                side_effect=RuntimeError("DB exploded"),
            ),
            _patch_db([uuid4()]),
        ):
            await handlers.on_animal_intake_completed(event)


# ---------------------------------------------------------------------------
# _notify_all_staff (DB integration)
# ---------------------------------------------------------------------------


class TestNotifyAllStaff:

    @pytest.mark.asyncio
    async def test_creates_notification_for_each_staff_user(self) -> None:
        handlers = _make_handlers()
        user_ids = [uuid4(), uuid4(), uuid4()]
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db(user_ids),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers._notify_all_staff(
                notification_type="test_type",
                title="Test",
                message="Hello",
                data={"key": "val"},
            )

        assert mock_create.call_count == 3
        called_user_ids = {c[1]["user_id"] for c in mock_create.call_args_list}
        assert called_user_ids == set(user_ids)

    @pytest.mark.asyncio
    async def test_does_nothing_when_no_staff_exist(self) -> None:
        handlers = _make_handlers()
        mock_create = AsyncMock(return_value=None)

        with (
            _patch_db([]),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            await handlers._notify_all_staff(
                notification_type="test_type",
                title="Test",
                message="Hello",
            )

        mock_create.assert_not_called()
