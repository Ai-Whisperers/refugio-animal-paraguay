"""Unit tests for subscription service layer.

Tests service functions with mocked Stripe API and database.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.db.models.subscription import SubscriptionStatus
from src.services.subscription_service import (
    _timestamp_to_datetime,
    cancel_subscription,
    create_subscription,
    get_subscription_stats,
    handle_subscription_updated,
    pause_subscription,
    record_payment_failure,
    resume_subscription,
    update_subscription_amount,
)


class TestTimestampToDatetime:
    """Tests for _timestamp_to_datetime helper."""

    def test_converts_valid_timestamp(self) -> None:
        # 2026-01-01 00:00:00 UTC
        result = _timestamp_to_datetime(1767225600)
        assert result is not None
        assert result.year == 2026
        assert result.tzinfo is not None

    def test_returns_none_for_none(self) -> None:
        assert _timestamp_to_datetime(None) is None


class TestCreateSubscription:
    """Tests for create_subscription service function."""

    @pytest.mark.asyncio
    async def test_creates_subscription_successfully(self) -> None:
        donor = MagicMock()
        donor.id = uuid4()
        donor.email = "donor@example.nl"
        donor.full_name = "Jan de Vries"

        db = AsyncMock()

        mock_customer_list = MagicMock()
        mock_customer_list.data = [MagicMock(id="cus_test123")]

        mock_price = MagicMock(id="price_test123")
        mock_sub = MagicMock(
            id="sub_test123",
            status="active",
            current_period_start=1767225600,
            current_period_end=1769817600,
        )

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
            patch("src.services.subscription_service.stripe") as mock_stripe,
            patch("src.services.subscription_service.Subscription") as mock_sub_cls,
            patch("src.services.subscription_service.Donation") as mock_don_cls,
        ):
            mock_stripe.Customer.list.return_value = mock_customer_list
            mock_stripe.PaymentMethod.attach = MagicMock()
            mock_stripe.Customer.modify = MagicMock()
            mock_stripe.Price.create.return_value = mock_price
            mock_stripe.Subscription.create.return_value = mock_sub

            mock_subscription_instance = MagicMock()
            mock_sub_cls.return_value = mock_subscription_instance
            mock_don_cls.return_value = MagicMock()

            result = await create_subscription(
                db=db,
                donor=donor,
                amount_cents=2000,
                currency="EUR",
                interval="month",
                payment_method_id="pm_card_visa",
            )

        assert result is not None
        # Verify db.add was called for subscription and donation
        assert db.add.call_count == 2
        assert db.flush.await_count >= 2

    @pytest.mark.asyncio
    async def test_raises_on_missing_stripe_key(self) -> None:
        donor = MagicMock()
        donor.id = uuid4()
        db = AsyncMock()

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""}),
            pytest.raises(ValueError, match="STRIPE_SECRET_KEY not configured"),
        ):
            await create_subscription(
                db=db,
                donor=donor,
                amount_cents=2000,
                currency="EUR",
                interval="month",
                payment_method_id="pm_card_visa",
            )


class TestCancelSubscription:
    """Tests for cancel_subscription service function."""

    @pytest.mark.asyncio
    async def test_cancel_at_period_end(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.notes = ""
        subscription.cancel_at_period_end = False

        db = AsyncMock()

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
            patch("src.services.subscription_service.stripe") as mock_stripe,
        ):
            mock_stripe.Subscription.modify = MagicMock()

            result = await cancel_subscription(
                db=db,
                subscription=subscription,
                cancel_immediately=False,
                reason="No longer needed",
            )

        assert result.cancel_at_period_end is True
        mock_stripe.Subscription.modify.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_immediately(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.notes = ""
        subscription.canceled_at = None

        db = AsyncMock()

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
            patch("src.services.subscription_service.stripe") as mock_stripe,
        ):
            mock_stripe.Subscription.cancel = MagicMock()

            result = await cancel_subscription(
                db=db,
                subscription=subscription,
                cancel_immediately=True,
            )

        assert result.status == SubscriptionStatus.CANCELED.value
        mock_stripe.Subscription.cancel.assert_called_once()


class TestHandleSubscriptionUpdated:
    """Tests for handle_subscription_updated webhook handler helper."""

    @pytest.mark.asyncio
    async def test_updates_status(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.canceled_at = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        db.execute.return_value = mock_result

        result = await handle_subscription_updated(
            db=db,
            stripe_subscription_id="sub_test123",
            new_status="past_due",
        )

        assert result == "updated_past_due"
        assert subscription.status == "past_due"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sets_canceled_at_on_cancellation(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.canceled_at = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        db.execute.return_value = mock_result

        result = await handle_subscription_updated(
            db=db,
            stripe_subscription_id="sub_test123",
            new_status="canceled",
        )

        assert result == "updated_canceled"
        assert subscription.canceled_at is not None

    @pytest.mark.asyncio
    async def test_returns_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await handle_subscription_updated(
            db=db,
            stripe_subscription_id="sub_unknown",
            new_status="active",
        )

        assert result == "subscription_not_found"

    @pytest.mark.asyncio
    async def test_updates_period_fields(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.canceled_at = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        db.execute.return_value = mock_result

        await handle_subscription_updated(
            db=db,
            stripe_subscription_id="sub_test123",
            new_status="active",
            current_period_start=1767225600,
            current_period_end=1769817600,
            cancel_at_period_end=False,
        )

        assert subscription.current_period_start is not None
        assert subscription.current_period_end is not None
        assert subscription.cancel_at_period_end is False


class TestRecordPaymentFailure:
    """Tests for record_payment_failure service function."""

    @pytest.mark.asyncio
    async def test_increments_failure_count(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.failed_payment_count = 0
        subscription.id = uuid4()
        subscription.donor_id = uuid4()
        subscription.notes = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        db.execute.return_value = mock_result

        result = await record_payment_failure(
            db=db,
            stripe_subscription_id="sub_test123",
            error_message="Card declined",
        )

        assert result["action"] == "payment_failure_recorded"
        assert result["failed_count"] == 1
        assert subscription.failed_payment_count == 1
        assert subscription.last_payment_error == "Card declined"
        assert subscription.status == SubscriptionStatus.PAST_DUE.value

    @pytest.mark.asyncio
    async def test_returns_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await record_payment_failure(
            db=db,
            stripe_subscription_id="sub_unknown",
        )

        assert result["action"] == "subscription_not_found"

    @pytest.mark.asyncio
    async def test_auto_cancels_after_max_failures(self) -> None:
        """After MAX_FAILED_PAYMENT_ATTEMPTS, subscription should auto-cancel."""
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.failed_payment_count = 2  # Will become 3 (MAX)
        subscription.id = uuid4()
        subscription.donor_id = uuid4()
        subscription.notes = ""
        subscription.canceled_at = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        db.execute.return_value = mock_result

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
            patch("src.services.subscription_service.stripe") as mock_stripe,
        ):
            mock_stripe.Subscription.cancel = MagicMock()

            result = await record_payment_failure(
                db=db,
                stripe_subscription_id="sub_test123",
                error_message="Card declined again",
            )

        assert result["action"] == "subscription_cancelled"
        assert subscription.status == SubscriptionStatus.CANCELED.value
        assert subscription.canceled_at is not None
        assert "Auto-cancelled" in (subscription.notes or "")
        mock_stripe.Subscription.cancel.assert_called_once_with("sub_test123")

    @pytest.mark.asyncio
    async def test_does_not_cancel_before_max_failures(self) -> None:
        """Before MAX_FAILED_PAYMENT_ATTEMPTS, subscription stays past_due."""
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.failed_payment_count = 1  # Will become 2 (not max)
        subscription.id = uuid4()
        subscription.donor_id = uuid4()
        subscription.notes = None

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = subscription
        db.execute.return_value = mock_result

        result = await record_payment_failure(
            db=db,
            stripe_subscription_id="sub_test123",
            error_message="Insufficient funds",
        )

        assert result["action"] == "payment_failure_recorded"
        assert subscription.status == SubscriptionStatus.PAST_DUE.value


class TestPauseSubscription:
    """Tests for pause_subscription service function."""

    @pytest.mark.asyncio
    async def test_pauses_subscription(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"

        db = AsyncMock()

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
            patch("src.services.subscription_service.stripe") as mock_stripe,
        ):
            mock_stripe.Subscription.modify = MagicMock()

            result = await pause_subscription(db, subscription)

        assert result.status == SubscriptionStatus.PAUSED.value
        mock_stripe.Subscription.modify.assert_called_once()


class TestResumeSubscription:
    """Tests for resume_subscription service function."""

    @pytest.mark.asyncio
    async def test_resumes_subscription(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"

        db = AsyncMock()

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
            patch("src.services.subscription_service.stripe") as mock_stripe,
        ):
            mock_stripe.Subscription.modify = MagicMock()

            result = await resume_subscription(db, subscription)

        assert result.status == SubscriptionStatus.ACTIVE.value
        mock_stripe.Subscription.modify.assert_called_once()


class TestUpdateSubscriptionAmount:
    """Tests for update_subscription_amount service function."""

    @pytest.mark.asyncio
    async def test_updates_amount(self) -> None:
        subscription = MagicMock()
        subscription.stripe_subscription_id = "sub_test123"
        subscription.interval = "month"
        subscription.currency = "EUR"

        db = AsyncMock()

        mock_price = MagicMock(id="price_new123")
        mock_stripe_sub = MagicMock()
        mock_stripe_sub.__getitem__ = lambda self, key: {
            "items": {"data": [{"id": "si_item123"}]}
        }.get(key)
        mock_stripe_sub.get = lambda key, default=None: {
            "items": {"data": [{"id": "si_item123"}]}
        }.get(key, default)

        with (
            patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_fake"}),
            patch("src.services.subscription_service.stripe") as mock_stripe,
        ):
            mock_stripe.Price.create.return_value = mock_price
            mock_stripe.Subscription.retrieve.return_value = mock_stripe_sub
            mock_stripe.Subscription.modify = MagicMock()

            result = await update_subscription_amount(db, subscription, 5000)

        assert result.amount_cents == 5000
        assert result.stripe_price_id == "price_new123"


class TestGetSubscriptionStats:
    """Tests for get_subscription_stats."""

    @pytest.mark.asyncio
    async def test_returns_stats_dict(self) -> None:
        db = AsyncMock()

        # Mock status counts result
        status_rows = [
            MagicMock(status="active", count=10),
            MagicMock(status="canceled", count=3),
            MagicMock(status="past_due", count=1),
        ]
        # Mock monthly/yearly scalar results
        monthly_result = MagicMock()
        monthly_result.scalar.return_value = 50000
        yearly_result = MagicMock()
        yearly_result.scalar.return_value = 120000

        db.execute.side_effect = [
            MagicMock(__iter__=lambda s: iter(status_rows)),
            monthly_result,
            yearly_result,
        ]

        stats = await get_subscription_stats(db)

        assert stats["total_active"] == 10
        assert stats["total_canceled"] == 3
        assert stats["total_past_due"] == 1
        assert stats["total_paused"] == 0
        assert stats["monthly_recurring_cents"] == 50000
        assert stats["yearly_recurring_cents"] == 120000
