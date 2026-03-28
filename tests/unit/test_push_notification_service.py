"""Unit tests for push notification service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.push_notification_service import (
    BODY_MAX_LENGTH,
    MAX_FAILURE_COUNT,
    TITLE_MAX_LENGTH,
    VALID_PUSH_CATEGORIES,
    DuplicateSubscriptionError,
    InvalidPushCategoryError,
    PushNotificationError,
    SubscriptionNotFoundError,
    create_subscription,
    deactivate_subscription,
    get_active_subscriptions_batch,
    get_donor_subscriptions,
    get_push_stats,
    prepare_push_payload,
    record_push_result,
    validate_push_category,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_subscription(**overrides):
    """Create a mock PushSubscription with sensible defaults."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "donor_id": uuid4(),
        "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
        "p256dh_key": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8p8hC5TRs",
        "auth_key": "tBHItJI5svbpC7s3bW9z3Q",
        "user_agent": "Mozilla/5.0",
        "is_active": True,
        "failure_count": 0,
        "last_used_at": None,
        "created_at": now,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for push notification error hierarchy."""

    def test_push_notification_error_base(self) -> None:
        err = PushNotificationError("test", details="detail")
        assert err.message == "test"
        assert err.details == "detail"

    def test_subscription_not_found(self) -> None:
        err = SubscriptionNotFoundError("abc-123")
        assert "abc-123" in err.details

    def test_invalid_push_category(self) -> None:
        err = InvalidPushCategoryError("invalid_cat")
        assert "invalid_cat" in err.details

    def test_duplicate_subscription(self) -> None:
        donor_id = uuid4()
        err = DuplicateSubscriptionError(donor_id)
        assert str(donor_id) in err.details


# ---------------------------------------------------------------------------
# validate_push_category
# ---------------------------------------------------------------------------


class TestValidatePushCategory:
    """Tests for push category validation."""

    def test_valid_categories(self) -> None:
        for cat in VALID_PUSH_CATEGORIES:
            validate_push_category(cat)  # should not raise

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(InvalidPushCategoryError):
            validate_push_category("invalid_category")

    def test_empty_category_raises(self) -> None:
        with pytest.raises(InvalidPushCategoryError):
            validate_push_category("")


# ---------------------------------------------------------------------------
# create_subscription
# ---------------------------------------------------------------------------


class TestCreateSubscription:
    """Tests for create_subscription."""

    @pytest.mark.asyncio
    async def test_creates_new_subscription(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        sub = await create_subscription(
            donor_id=uuid4(),
            endpoint="https://fcm.googleapis.com/fcm/send/test",
            p256dh_key="test_p256dh",
            auth_key="test_auth",
            db=db,
        )

        assert sub.endpoint == "https://fcm.googleapis.com/fcm/send/test"
        assert sub.p256dh_key == "test_p256dh"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reactivates_inactive_subscription(self) -> None:
        existing = _make_subscription(is_active=False, failure_count=3)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        sub = await create_subscription(
            donor_id=existing.donor_id,
            endpoint=existing.endpoint,
            p256dh_key="new_key",
            auth_key="new_auth",
            db=db,
        )

        assert sub.is_active is True
        assert sub.p256dh_key == "new_key"
        assert sub.failure_count == 0

    @pytest.mark.asyncio
    async def test_duplicate_active_raises(self) -> None:
        existing = _make_subscription(is_active=True)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = mock_result

        with pytest.raises(DuplicateSubscriptionError):
            await create_subscription(
                donor_id=existing.donor_id,
                endpoint=existing.endpoint,
                p256dh_key="key",
                auth_key="auth",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_invalid_endpoint_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PushNotificationError, match="Invalid endpoint"):
            await create_subscription(
                donor_id=uuid4(),
                endpoint="http://insecure.example.com",
                p256dh_key="key",
                auth_key="auth",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_empty_endpoint_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PushNotificationError, match="Invalid endpoint"):
            await create_subscription(
                donor_id=uuid4(),
                endpoint="",
                p256dh_key="key",
                auth_key="auth",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_missing_p256dh_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PushNotificationError, match="Missing p256dh"):
            await create_subscription(
                donor_id=uuid4(),
                endpoint="https://push.example.com/send/123",
                p256dh_key="",
                auth_key="auth",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_missing_auth_key_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PushNotificationError, match="Missing auth"):
            await create_subscription(
                donor_id=uuid4(),
                endpoint="https://push.example.com/send/123",
                p256dh_key="key",
                auth_key="",
                db=db,
            )


# ---------------------------------------------------------------------------
# deactivate_subscription
# ---------------------------------------------------------------------------


class TestDeactivateSubscription:
    """Tests for deactivate_subscription."""

    @pytest.mark.asyncio
    async def test_deactivates_subscription(self) -> None:
        sub = _make_subscription(is_active=True)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sub
        db.execute.return_value = mock_result

        result = await deactivate_subscription(
            subscription_id=sub.id,
            donor_id=sub.donor_id,
            db=db,
        )
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(SubscriptionNotFoundError):
            await deactivate_subscription(
                subscription_id=uuid4(),
                donor_id=uuid4(),
                db=db,
            )


# ---------------------------------------------------------------------------
# get_donor_subscriptions
# ---------------------------------------------------------------------------


class TestGetDonorSubscriptions:
    """Tests for get_donor_subscriptions."""

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        subs = [_make_subscription(), _make_subscription()]
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = subs
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await get_donor_subscriptions(uuid4(), db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await get_donor_subscriptions(uuid4(), db)
        assert result == []


# ---------------------------------------------------------------------------
# get_active_subscriptions_batch
# ---------------------------------------------------------------------------


class TestGetActiveSubscriptionsBatch:
    """Tests for get_active_subscriptions_batch."""

    @pytest.mark.asyncio
    async def test_returns_batch(self) -> None:
        subs = [_make_subscription() for _ in range(3)]
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = subs
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await get_active_subscriptions_batch(db, limit=10)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# record_push_result
# ---------------------------------------------------------------------------


class TestRecordPushResult:
    """Tests for record_push_result."""

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self) -> None:
        db = AsyncMock()
        await record_push_result(
            subscription_id=uuid4(),
            success=True,
            db=db,
        )
        db.execute.assert_awaited_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_failure_increments_count(self) -> None:
        sub = _make_subscription(failure_count=2)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sub
        # First call: update, second call: select
        db.execute.side_effect = [MagicMock(), mock_result]

        await record_push_result(
            subscription_id=sub.id,
            success=False,
            db=db,
        )
        assert db.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_failure_deactivates_at_threshold(self) -> None:
        sub = _make_subscription(failure_count=MAX_FAILURE_COUNT)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sub
        db.execute.side_effect = [MagicMock(), mock_result]

        await record_push_result(
            subscription_id=sub.id,
            success=False,
            db=db,
        )
        assert sub.is_active is False


# ---------------------------------------------------------------------------
# prepare_push_payload
# ---------------------------------------------------------------------------


class TestPreparePushPayload:
    """Tests for prepare_push_payload."""

    @pytest.mark.asyncio
    async def test_valid_payload(self) -> None:
        payload = await prepare_push_payload(
            category="emergency_created",
            title="New Emergency",
            body="An injured dog needs help!",
            url="/emergencies/123",
        )
        assert payload["category"] == "emergency_created"
        assert payload["title"] == "New Emergency"
        assert payload["url"] == "/emergencies/123"

    @pytest.mark.asyncio
    async def test_invalid_category_raises(self) -> None:
        with pytest.raises(InvalidPushCategoryError):
            await prepare_push_payload(
                category="invalid",
                title="Test",
                body="Test body",
            )

    @pytest.mark.asyncio
    async def test_title_too_long_raises(self) -> None:
        with pytest.raises(PushNotificationError, match="Title too long"):
            await prepare_push_payload(
                category="emergency_created",
                title="A" * (TITLE_MAX_LENGTH + 1),
                body="Test body",
            )

    @pytest.mark.asyncio
    async def test_body_too_long_raises(self) -> None:
        with pytest.raises(PushNotificationError, match="Body too long"):
            await prepare_push_payload(
                category="emergency_created",
                title="Test",
                body="B" * (BODY_MAX_LENGTH + 1),
            )

    @pytest.mark.asyncio
    async def test_payload_without_optional_fields(self) -> None:
        payload = await prepare_push_payload(
            category="donation_confirmation",
            title="Thank you!",
            body="Your donation was received.",
        )
        assert "url" not in payload
        assert "data" not in payload

    @pytest.mark.asyncio
    async def test_payload_with_data(self) -> None:
        payload = await prepare_push_payload(
            category="campaign_milestone",
            title="Milestone!",
            body="Campaign reached 50%!",
            data={"campaign_id": "abc-123", "progress": 50},
        )
        assert payload["data"]["campaign_id"] == "abc-123"


# ---------------------------------------------------------------------------
# get_push_stats
# ---------------------------------------------------------------------------


class TestGetPushStats:
    """Tests for get_push_stats."""

    @pytest.mark.asyncio
    async def test_returns_stats(self) -> None:
        db = AsyncMock()
        # Three scalar_one calls: total, active, with_failures
        total_result = MagicMock()
        total_result.scalar_one.return_value = 100
        active_result = MagicMock()
        active_result.scalar_one.return_value = 80
        failed_result = MagicMock()
        failed_result.scalar_one.return_value = 5

        db.execute.side_effect = [total_result, active_result, failed_result]

        stats = await get_push_stats(db)
        assert stats["total_subscriptions"] == 100
        assert stats["active_subscriptions"] == 80
        assert stats["inactive_subscriptions"] == 20
        assert stats["active_with_failures"] == 5
