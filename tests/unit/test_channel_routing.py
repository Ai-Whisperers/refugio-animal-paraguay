"""Unit tests for channel routing based on notification preferences.

Tests that in-app and email notification dispatchers honour per-user
opt-out preferences before creating / sending notifications.

RAP-207: Channel routing based on preferences
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.events.types import DomainEvent, EventType
from src.notifications.handlers import NotificationHandlers
from src.notifications.in_app_handlers import InAppNotificationHandlers

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_USER_A = uuid.uuid4()  # has in_app/email enabled
_USER_B = uuid.uuid4()  # has in_app/email disabled

EMAIL_A = "staff-a@example.com"
EMAIL_B = "staff-b@example.com"


def _make_event(event_type: EventType, payload: dict | None = None) -> DomainEvent:
    return DomainEvent(
        id=uuid.uuid4(),
        event_type=event_type,
        aggregate_id=uuid.uuid4(),
        payload=payload or {},
    )


# ---------------------------------------------------------------------------
# In-app channel routing
# ---------------------------------------------------------------------------


class TestInAppChannelRouting:
    """_notify_all_staff must gate on each user's in_app preference."""

    @pytest.mark.asyncio
    async def test_user_with_disabled_in_app_skipped(self) -> None:
        """A user who opts out of in_app should not receive a notification."""
        event = _make_event(
            EventType.ADOPTION_REQUEST_CREATED,
            {"adopter_name": "Ana", "animal_name": "Rex"},
        )

        mock_create = AsyncMock()

        # User B has in_app disabled, User A has it enabled
        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return user_id == _USER_A

        with (
            patch(
                "src.notifications.in_app_handlers.get_async_session",
                return_value=_make_session_ctx([_USER_A, _USER_B]),
            ),
            patch(
                "src.notifications.in_app_handlers.is_notification_enabled",
                side_effect=fake_is_enabled,
            ),
            patch(
                "src.notifications.in_app_handlers.create_notification",
                mock_create,
            ),
        ):
            handler = InAppNotificationHandlers()
            await handler.on_adoption_request_created(event)

        # Only User A should receive the notification
        assert mock_create.call_count == 1
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["user_id"] == _USER_A

    @pytest.mark.asyncio
    async def test_user_with_enabled_in_app_notified(self) -> None:
        """A user who has in_app enabled should receive the notification."""
        event = _make_event(
            EventType.DONATION_RECEIVED,
            {"donor_name": "Maria", "amount": "100", "currency": "EUR"},
        )
        mock_create = AsyncMock()

        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return True  # both users enabled

        with (
            patch(
                "src.notifications.in_app_handlers.get_async_session",
                return_value=_make_session_ctx([_USER_A, _USER_B]),
            ),
            patch(
                "src.notifications.in_app_handlers.is_notification_enabled",
                side_effect=fake_is_enabled,
            ),
            patch(
                "src.notifications.in_app_handlers.create_notification",
                mock_create,
            ),
        ):
            handler = InAppNotificationHandlers()
            await handler.on_donation_received(event)

        assert mock_create.call_count == 2

    @pytest.mark.asyncio
    async def test_missing_preference_treated_as_enabled(self) -> None:
        """is_notification_enabled returns True when no row exists — notification sent."""
        event = _make_event(
            EventType.ANIMAL_INTAKE_COMPLETED,
            {"animal_name": "Luna", "species": "cat"},
        )
        mock_create = AsyncMock()

        # is_notification_enabled always returns True (missing row = enabled)
        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return True

        with (
            patch(
                "src.notifications.in_app_handlers.get_async_session",
                return_value=_make_session_ctx([_USER_A]),
            ),
            patch(
                "src.notifications.in_app_handlers.is_notification_enabled",
                side_effect=fake_is_enabled,
            ),
            patch(
                "src.notifications.in_app_handlers.create_notification",
                mock_create,
            ),
        ):
            handler = InAppNotificationHandlers()
            await handler.on_animal_intake_completed(event)

        assert mock_create.call_count == 1

    @pytest.mark.asyncio
    async def test_all_users_disabled_creates_no_notifications(self) -> None:
        """When all users opt out, no notifications are created."""
        event = _make_event(
            EventType.ADOPTION_STATUS_CHANGED,
            {"old_status": "pending", "new_status": "approved"},
        )
        mock_create = AsyncMock()

        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return False  # all opted out

        with (
            patch(
                "src.notifications.in_app_handlers.get_async_session",
                return_value=_make_session_ctx([_USER_A, _USER_B]),
            ),
            patch(
                "src.notifications.in_app_handlers.is_notification_enabled",
                side_effect=fake_is_enabled,
            ),
            patch(
                "src.notifications.in_app_handlers.create_notification",
                mock_create,
            ),
        ):
            handler = InAppNotificationHandlers()
            await handler.on_adoption_status_changed(event)

        assert mock_create.call_count == 0

    @pytest.mark.asyncio
    async def test_no_staff_users_no_notifications(self) -> None:
        """When there are no staff users, no notifications are created."""
        event = _make_event(EventType.ADOPTION_REQUEST_CREATED)
        mock_create = AsyncMock()

        with (
            patch(
                "src.notifications.in_app_handlers.get_async_session",
                return_value=_make_session_ctx([]),  # empty staff list
            ),
            patch("src.notifications.in_app_handlers.create_notification", mock_create),
        ):
            handler = InAppNotificationHandlers()
            await handler.on_adoption_request_created(event)

        assert mock_create.call_count == 0


# ---------------------------------------------------------------------------
# Email channel routing
# ---------------------------------------------------------------------------


class TestEmailChannelRouting:
    """_get_staff_email_recipients must gate on each user's email preference."""

    @pytest.mark.asyncio
    async def test_opted_out_staff_not_emailed(self) -> None:
        """Staff user who opts out of email should not receive the alert."""
        event = _make_event(
            EventType.ADOPTION_REQUEST_CREATED,
            {"adopter_email": None, "adopter_name": "Carlos", "animal_name": "Bolt"},
        )

        mock_send = AsyncMock()
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "<html>body</html>"
        mock_email_service = MagicMock()
        mock_email_service.send_email = mock_send

        # User A: email enabled; User B: email disabled
        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return user_id == _USER_A

        with patch(
            "src.notifications.handlers.get_async_session",
            return_value=_make_session_ctx_with_emails(
                [(_USER_A, EMAIL_A), (_USER_B, EMAIL_B)]
            ),
        ), patch(
            "src.notifications.handlers.is_notification_enabled",
            side_effect=fake_is_enabled,
        ):
            handler = NotificationHandlers(mock_email_service, mock_renderer)
            await handler.on_adoption_request_created(event)

        # Only EMAIL_A should receive the staff alert
        sent_to = [call.args[0].to for call in mock_send.call_args_list]
        assert EMAIL_A in sent_to
        assert EMAIL_B not in sent_to

    @pytest.mark.asyncio
    async def test_all_staff_opted_in_receive_email(self) -> None:
        """All staff receive alert when all have email enabled."""
        event = _make_event(
            EventType.ADOPTION_REQUEST_CREATED,
            {"adopter_email": None, "adopter_name": "Sofia", "animal_name": "Max"},
        )

        mock_send = AsyncMock()
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "<html>body</html>"
        mock_email_service = MagicMock()
        mock_email_service.send_email = mock_send

        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return True

        with patch(
            "src.notifications.handlers.get_async_session",
            return_value=_make_session_ctx_with_emails(
                [(_USER_A, EMAIL_A), (_USER_B, EMAIL_B)]
            ),
        ), patch(
            "src.notifications.handlers.is_notification_enabled",
            side_effect=fake_is_enabled,
        ):
            handler = NotificationHandlers(mock_email_service, mock_renderer)
            await handler.on_adoption_request_created(event)

        sent_to = [call.args[0].to for call in mock_send.call_args_list]
        assert EMAIL_A in sent_to
        assert EMAIL_B in sent_to

    @pytest.mark.asyncio
    async def test_all_staff_opted_out_sends_no_alert(self) -> None:
        """No staff alert is sent when all staff have email disabled."""
        event = _make_event(
            EventType.ADOPTION_REQUEST_CREATED,
            {"adopter_email": None, "adopter_name": "Luisa", "animal_name": "Nemo"},
        )

        mock_send = AsyncMock()
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "<html>body</html>"
        mock_email_service = MagicMock()
        mock_email_service.send_email = mock_send

        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return False  # all opted out

        with patch(
            "src.notifications.handlers.get_async_session",
            return_value=_make_session_ctx_with_emails(
                [(_USER_A, EMAIL_A), (_USER_B, EMAIL_B)]
            ),
        ), patch(
            "src.notifications.handlers.is_notification_enabled",
            side_effect=fake_is_enabled,
        ):
            handler = NotificationHandlers(mock_email_service, mock_renderer)
            await handler.on_adoption_request_created(event)

        # No staff alert emails sent (adopter_email was None so adopter email also skipped)
        assert mock_send.call_count == 0

    @pytest.mark.asyncio
    async def test_adopter_email_sent_regardless_of_staff_preferences(self) -> None:
        """Adopter confirmation email is not gated by staff preferences."""
        event = _make_event(
            EventType.ADOPTION_REQUEST_CREATED,
            {
                "adopter_email": "adopter@example.com",
                "adopter_name": "Pedro",
                "animal_name": "Tito",
            },
        )

        mock_send = AsyncMock()
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = "<html>body</html>"
        mock_email_service = MagicMock()
        mock_email_service.send_email = mock_send

        # All staff opted out
        async def fake_is_enabled(db, *, user_id, notification_type, channel):
            return False

        with patch(
            "src.notifications.handlers.get_async_session",
            return_value=_make_session_ctx_with_emails(
                [(_USER_A, EMAIL_A)]
            ),
        ), patch(
            "src.notifications.handlers.is_notification_enabled",
            side_effect=fake_is_enabled,
        ):
            handler = NotificationHandlers(mock_email_service, mock_renderer)
            await handler.on_adoption_request_created(event)

        # Adopter confirmation should still be sent
        sent_to = [call.args[0].to for call in mock_send.call_args_list]
        assert "adopter@example.com" in sent_to
        assert EMAIL_A not in sent_to  # staff was opted out


# ---------------------------------------------------------------------------
# Context manager helpers
# ---------------------------------------------------------------------------


def _make_session_ctx(user_ids: list[uuid.UUID]):
    """Return an async context manager whose __aenter__ yields a fake session.

    The session.execute() returns user_ids as scalars (for the in_app handler).
    """

    class FakeResult:
        def __init__(self, ids):
            self._ids = ids

        def scalars(self):
            return self

        def all(self):
            return self._ids

    class FakeSession:
        async def execute(self, stmt):
            return FakeResult(user_ids)

    class FakeCtx:
        async def __aenter__(self):
            return FakeSession()

        async def __aexit__(self, *args):
            pass

    return FakeCtx()


def _make_session_ctx_with_emails(rows: list[tuple[uuid.UUID, str]]):
    """Return an async context manager whose session returns (id, email) rows.

    Used for email handlers that select User.id + User.email together.
    """

    class FakeRow:
        def __init__(self, uid, email):
            self.user_id = uid
            self.email = email

        def __iter__(self):
            return iter((self.user_id, self.email))

    class FakeResult:
        def __init__(self, data):
            self._data = data

        def all(self):
            return [FakeRow(uid, email) for uid, email in self._data]

    class FakeSession:
        async def execute(self, stmt):
            return FakeResult(rows)

    class FakeCtx:
        async def __aenter__(self):
            return FakeSession()

        async def __aexit__(self, *args):
            pass

    return FakeCtx()
