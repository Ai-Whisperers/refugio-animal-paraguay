"""Unit tests for the Subscription model and its enums."""

from src.db.models.subscription import (
    Subscription,
    SubscriptionInterval,
    SubscriptionStatus,
)


class TestSubscriptionStatus:
    """Verify SubscriptionStatus enum values match expected Stripe statuses."""

    def test_active_value(self) -> None:
        assert SubscriptionStatus.ACTIVE.value == "active"

    def test_paused_value(self) -> None:
        assert SubscriptionStatus.PAUSED.value == "paused"

    def test_canceled_value(self) -> None:
        assert SubscriptionStatus.CANCELED.value == "canceled"

    def test_past_due_value(self) -> None:
        assert SubscriptionStatus.PAST_DUE.value == "past_due"

    def test_incomplete_value(self) -> None:
        assert SubscriptionStatus.INCOMPLETE.value == "incomplete"

    def test_trialing_value(self) -> None:
        assert SubscriptionStatus.TRIALING.value == "trialing"


class TestSubscriptionInterval:
    """Verify SubscriptionInterval enum values."""

    def test_month_value(self) -> None:
        assert SubscriptionInterval.MONTH.value == "month"

    def test_year_value(self) -> None:
        assert SubscriptionInterval.YEAR.value == "year"


class TestSubscriptionModel:
    """Verify Subscription model metadata."""

    def test_tablename(self) -> None:
        assert Subscription.__tablename__ == "subscriptions"

    def test_has_required_columns(self) -> None:
        column_names = {c.name for c in Subscription.__table__.columns}
        expected = {
            "id",
            "donor_id",
            "stripe_subscription_id",
            "stripe_customer_id",
            "stripe_price_id",
            "stripe_payment_method_id",
            "amount_cents",
            "currency",
            "interval",
            "status",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "canceled_at",
            "last_payment_error",
            "failed_payment_count",
            "notes",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(column_names)

    def test_stripe_subscription_id_is_unique(self) -> None:
        col = Subscription.__table__.c.stripe_subscription_id
        assert col.unique is True

    def test_donor_id_foreign_key(self) -> None:
        col = Subscription.__table__.c.donor_id
        fk = list(col.foreign_keys)
        assert len(fk) == 1
        assert fk[0].target_fullname == "donors.id"
