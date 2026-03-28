"""Unit tests for voucher notification service.

Tests notification creation, retry logic, rate limiting queries,
and donor notification listing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.db.models.voucher_notification import (
    MAX_RETRY_COUNT,
    NotificationChannel,
    NotificationStatus,
    VoucherNotification,
    VoucherNotificationType,
)
from src.services.voucher_notification_service import (
    RATE_LIMIT_MINUTES,
    NotificationNotFoundError,
    create_monthly_summary_notification,
    create_voucher_claimed_notification,
    create_voucher_redeemed_notification,
    get_donor_notifications,
    get_pending_notifications,
    mark_notification_failed,
    mark_notification_sent,
)

# --- Fixtures ---


def _make_notification(**overrides) -> VoucherNotification:
    """Create a VoucherNotification with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "event_type": VoucherNotificationType.VOUCHER_CLAIMED,
        "voucher_id": uuid4(),
        "channel": NotificationChannel.EMAIL,
        "status": NotificationStatus.PENDING,
        "retry_count": 0,
        "subject": "Test subject",
        "body_preview": "Test preview",
        "context_data": json.dumps({"key": "value"}),
        "created_at": datetime.now(UTC),
        "sent_at": None,
        "last_attempt_at": None,
    }
    defaults.update(overrides)
    notification = MagicMock(spec=VoucherNotification)
    for k, v in defaults.items():
        setattr(notification, k, v)
    return notification


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


# --- Enum Tests ---


class TestVoucherNotificationEnums:
    """Tests for notification enum values."""

    def test_notification_types(self) -> None:
        assert VoucherNotificationType.VOUCHER_CLAIMED == "voucher_claimed"
        assert VoucherNotificationType.VOUCHER_REDEEMED == "voucher_redeemed"
        assert VoucherNotificationType.MONTHLY_SUMMARY == "monthly_summary"

    def test_notification_channels(self) -> None:
        assert NotificationChannel.EMAIL == "email"
        assert NotificationChannel.WHATSAPP == "whatsapp"

    def test_notification_statuses(self) -> None:
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.FAILED == "failed"
        assert NotificationStatus.SKIPPED == "skipped"

    def test_max_retry_count(self) -> None:
        assert MAX_RETRY_COUNT == 3


class TestConstants:
    """Tests for service-level constants."""

    def test_rate_limit_minutes(self) -> None:
        assert RATE_LIMIT_MINUTES == 60
        assert RATE_LIMIT_MINUTES > 0


# --- create_voucher_claimed_notification ---


class TestCreateVoucherClaimedNotification:
    """Tests for voucher claimed notification creation."""

    @pytest.mark.asyncio
    async def test_creates_pending_notification(self) -> None:
        db = _mock_db()
        donor_id = uuid4()
        voucher_id = uuid4()

        # Patch VoucherNotification constructor to capture args
        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance

            await create_voucher_claimed_notification(
                db,
                donor_id=donor_id,
                voucher_id=voucher_id,
                rescuer_name="Maria",
                clinic_name="Clinica ABC",
                service_type="sterilization",
                animal_name="Luna",
            )

            mock_cls.assert_called_once()
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["user_id"] == donor_id
            assert call_kwargs["event_type"] == VoucherNotificationType.VOUCHER_CLAIMED
            assert call_kwargs["voucher_id"] == voucher_id
            assert call_kwargs["status"] == NotificationStatus.PENDING
            assert "Luna" in call_kwargs["body_preview"]
            assert "sterilization" in call_kwargs["body_preview"]
            db.add.assert_called_once_with(instance)
            db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_uses_default_animal_name_when_none(self) -> None:
        db = _mock_db()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_voucher_claimed_notification(
                db,
                donor_id=uuid4(),
                voucher_id=uuid4(),
                rescuer_name="Maria",
                clinic_name="Clinica ABC",
                service_type="vaccination",
                animal_name=None,
            )

            call_kwargs = mock_cls.call_args[1]
            assert "an animal in need" in call_kwargs["body_preview"]

    @pytest.mark.asyncio
    async def test_context_data_contains_rescuer_and_clinic(self) -> None:
        db = _mock_db()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_voucher_claimed_notification(
                db,
                donor_id=uuid4(),
                voucher_id=uuid4(),
                rescuer_name="Carlos",
                clinic_name="VetPy",
                service_type="checkup",
            )

            call_kwargs = mock_cls.call_args[1]
            context = json.loads(call_kwargs["context_data"])
            assert context["rescuer_name"] == "Carlos"
            assert context["clinic_name"] == "VetPy"
            assert context["service_type"] == "checkup"

    @pytest.mark.asyncio
    async def test_default_channel_is_email(self) -> None:
        db = _mock_db()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_voucher_claimed_notification(
                db,
                donor_id=uuid4(),
                voucher_id=uuid4(),
                rescuer_name="X",
                clinic_name="Y",
                service_type="Z",
            )

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["channel"] == NotificationChannel.EMAIL

    @pytest.mark.asyncio
    async def test_whatsapp_channel(self) -> None:
        db = _mock_db()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_voucher_claimed_notification(
                db,
                donor_id=uuid4(),
                voucher_id=uuid4(),
                rescuer_name="X",
                clinic_name="Y",
                service_type="Z",
                channel=NotificationChannel.WHATSAPP,
            )

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["channel"] == NotificationChannel.WHATSAPP


# --- create_voucher_redeemed_notification ---


class TestCreateVoucherRedeemedNotification:
    """Tests for voucher redeemed notification creation."""

    @pytest.mark.asyncio
    async def test_creates_redeemed_notification(self) -> None:
        db = _mock_db()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_voucher_redeemed_notification(
                db,
                donor_id=uuid4(),
                voucher_id=uuid4(),
                clinic_name="Clinica XYZ",
                service_type="surgery",
                animal_name="Max",
                proof_description="Photo of post-op recovery",
            )

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["event_type"] == VoucherNotificationType.VOUCHER_REDEEMED
            assert "surgery" in call_kwargs["body_preview"]
            assert "Max" in call_kwargs["body_preview"]

            context = json.loads(call_kwargs["context_data"])
            assert context["proof_description"] == "Photo of post-op recovery"

    @pytest.mark.asyncio
    async def test_subject_mentions_animal_help(self) -> None:
        db = _mock_db()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_voucher_redeemed_notification(
                db,
                donor_id=uuid4(),
                voucher_id=uuid4(),
                clinic_name="C",
                service_type="S",
            )

            call_kwargs = mock_cls.call_args[1]
            assert "animal" in call_kwargs["subject"].lower()


# --- create_monthly_summary_notification ---


class TestCreateMonthlySummaryNotification:
    """Tests for monthly summary notification creation."""

    @pytest.mark.asyncio
    async def test_creates_summary_notification(self) -> None:
        db = _mock_db()
        donor_id = uuid4()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_monthly_summary_notification(
                db,
                donor_id=donor_id,
                month=3,
                year=2026,
                total_purchased=10,
                total_redeemed=7,
                total_claimed=8,
                animals_helped=5,
                total_amount_eur=250.00,
            )

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["event_type"] == VoucherNotificationType.MONTHLY_SUMMARY
            assert call_kwargs["voucher_id"] is None
            assert "3/2026" in call_kwargs["subject"]
            assert "10 purchased" in call_kwargs["body_preview"]
            assert "5 animals helped" in call_kwargs["body_preview"]

    @pytest.mark.asyncio
    async def test_context_data_has_all_metrics(self) -> None:
        db = _mock_db()

        with patch("src.services.voucher_notification_service.VoucherNotification") as mock_cls:
            mock_cls.return_value = MagicMock()

            await create_monthly_summary_notification(
                db,
                donor_id=uuid4(),
                month=12,
                year=2025,
                total_purchased=5,
                total_redeemed=3,
                total_claimed=4,
                animals_helped=2,
                total_amount_eur=100.50,
            )

            call_kwargs = mock_cls.call_args[1]
            context = json.loads(call_kwargs["context_data"])
            assert context["month"] == 12
            assert context["year"] == 2025
            assert context["total_purchased"] == 5
            assert context["total_redeemed"] == 3
            assert context["total_claimed"] == 4
            assert context["animals_helped"] == 2
            assert context["total_amount_eur"] == 100.50


# --- get_pending_notifications ---


class TestGetPendingNotifications:
    """Tests for pending notification retrieval with rate limiting."""

    @pytest.mark.asyncio
    async def test_returns_pending_notifications(self) -> None:
        db = _mock_db()
        notifications = [_make_notification(), _make_notification()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = notifications
        db.execute.return_value = mock_result

        result = await get_pending_notifications(db, limit=50)

        assert len(result) == 2
        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_respects_limit_parameter(self) -> None:
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        await get_pending_notifications(db, limit=10)

        db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_none_pending(self) -> None:
        db = _mock_db()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await get_pending_notifications(db)

        assert result == []


# --- mark_notification_sent ---


class TestMarkNotificationSent:
    """Tests for marking notifications as sent."""

    @pytest.mark.asyncio
    async def test_executes_update_and_flushes(self) -> None:
        db = _mock_db()
        notification_id = uuid4()

        await mark_notification_sent(db, notification_id)

        db.execute.assert_awaited_once()
        db.flush.assert_awaited_once()


# --- mark_notification_failed ---


class TestMarkNotificationFailed:
    """Tests for marking notifications as failed with retry logic."""

    @pytest.mark.asyncio
    async def test_increments_retry_count(self) -> None:
        db = _mock_db()
        notification_id = uuid4()

        # Mock the SELECT to return current retry_count
        mock_row = MagicMock()
        mock_row.retry_count = 0
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = mock_row
        db.execute.return_value = mock_result

        await mark_notification_failed(db, notification_id)

        # Should have been called twice: SELECT + UPDATE
        assert db.execute.await_count == 2
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stays_pending_when_below_max_retries(self) -> None:
        db = _mock_db()
        notification_id = uuid4()

        mock_row = MagicMock()
        mock_row.retry_count = 1  # Will become 2, still below MAX_RETRY_COUNT=3
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = mock_row
        db.execute.return_value = mock_result

        await mark_notification_failed(db, notification_id)

        # Verify the UPDATE was called (second execute)
        assert db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_marks_failed_at_max_retries(self) -> None:
        db = _mock_db()
        notification_id = uuid4()

        mock_row = MagicMock()
        mock_row.retry_count = MAX_RETRY_COUNT - 1  # Will hit max
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = mock_row
        db.execute.return_value = mock_result

        await mark_notification_failed(db, notification_id)

        assert db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_notification(self) -> None:
        db = _mock_db()
        notification_id = uuid4()

        mock_result = MagicMock()
        mock_result.one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(NotificationNotFoundError) as exc_info:
            await mark_notification_failed(db, notification_id)

        assert exc_info.value.notification_id == notification_id


# --- get_donor_notifications ---


class TestGetDonorNotifications:
    """Tests for paginated donor notification listing."""

    @pytest.mark.asyncio
    async def test_returns_notifications_and_total(self) -> None:
        db = _mock_db()
        donor_id = uuid4()
        notifications = [_make_notification(user_id=donor_id)]

        # First call returns notifications, second returns count
        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = notifications

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        db.execute.side_effect = [mock_list_result, mock_count_result]

        result_notifs, total = await get_donor_notifications(
            db, donor_id=donor_id, page=1, page_size=20
        )

        assert len(result_notifs) == 1
        assert total == 1

    @pytest.mark.asyncio
    async def test_pagination_parameters(self) -> None:
        db = _mock_db()
        donor_id = uuid4()

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0

        db.execute.side_effect = [mock_list_result, mock_count_result]

        result_notifs, total = await get_donor_notifications(
            db, donor_id=donor_id, page=3, page_size=10
        )

        assert result_notifs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_default_pagination(self) -> None:
        db = _mock_db()
        donor_id = uuid4()

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0
        db.execute.side_effect = [mock_list_result, mock_count_result]

        result_notifs, total = await get_donor_notifications(db, donor_id=donor_id)

        assert result_notifs == []
        assert total == 0


# --- NotificationNotFoundError ---


class TestNotificationNotFoundError:
    """Tests for the NotificationNotFoundError exception."""

    def test_stores_notification_id(self) -> None:
        nid = uuid4()
        error = NotificationNotFoundError(nid)
        assert error.notification_id == nid

    def test_message_contains_id(self) -> None:
        nid = uuid4()
        error = NotificationNotFoundError(nid)
        assert str(nid) in error.message

    def test_is_exception(self) -> None:
        error = NotificationNotFoundError(uuid4())
        assert isinstance(error, Exception)
