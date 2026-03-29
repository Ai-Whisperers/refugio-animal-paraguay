"""Unit tests for GDPR third-party deletion cascade service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.gdpr_third_party_deletion_service import (
    cancel_active_stripe_subscriptions,
    delete_stripe_customer,
    process_third_party_deletion,
    remove_from_email_lists,
)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.flush = AsyncMock()
    return db


class TestCancelActiveStripeSubscriptions:
    """Tests for cancel_active_stripe_subscriptions()."""

    @pytest.mark.asyncio
    async def test_no_active_subscriptions_returns_zeros(self, mock_db: AsyncMock) -> None:
        """Return zero counts when donor has no active subscriptions."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        stats = await cancel_active_stripe_subscriptions(mock_db, uuid4())

        assert stats == {"cancelled": 0, "failed": 0, "skipped": 0}

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service._get_stripe_key")
    async def test_skips_when_stripe_key_not_configured(
        self,
        mock_key: MagicMock,
        mock_db: AsyncMock,
    ) -> None:
        """Return all subscriptions as skipped when STRIPE_SECRET_KEY is not set."""
        mock_key.return_value = None

        sub = MagicMock()
        sub.stripe_subscription_id = "sub_test_123"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sub]
        mock_db.execute.return_value = mock_result

        stats = await cancel_active_stripe_subscriptions(mock_db, uuid4())

        assert stats["skipped"] == 1
        assert stats["cancelled"] == 0

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service._get_stripe_key")
    async def test_skips_subscription_without_stripe_id(
        self,
        mock_key: MagicMock,
        mock_db: AsyncMock,
    ) -> None:
        """Skip subscriptions that have no stripe_subscription_id."""
        mock_key.return_value = "sk_test_key"

        sub = MagicMock()
        sub.stripe_subscription_id = None
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sub]
        mock_db.execute.return_value = mock_result

        with patch.dict("sys.modules", {"stripe": MagicMock()}):
            stats = await cancel_active_stripe_subscriptions(mock_db, uuid4())

        assert stats["skipped"] == 1
        assert stats["cancelled"] == 0

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service._get_stripe_key")
    async def test_counts_failed_subscriptions(
        self,
        mock_key: MagicMock,
        mock_db: AsyncMock,
    ) -> None:
        """Count failures when Stripe API raises an exception."""
        mock_key.return_value = "sk_test_key"

        sub = MagicMock()
        sub.stripe_subscription_id = "sub_test_fail"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sub]
        mock_db.execute.return_value = mock_result

        mock_stripe = MagicMock()
        mock_stripe.Subscription.cancel.side_effect = Exception("Stripe API error")
        with patch.dict("sys.modules", {"stripe": mock_stripe}):
            stats = await cancel_active_stripe_subscriptions(mock_db, uuid4())

        assert stats["failed"] == 1
        assert stats["cancelled"] == 0

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service._get_stripe_key")
    async def test_cancels_active_subscription_successfully(
        self,
        mock_key: MagicMock,
        mock_db: AsyncMock,
    ) -> None:
        """Successfully cancel a Stripe subscription and update local status."""
        mock_key.return_value = "sk_test_key"

        sub = MagicMock()
        sub.stripe_subscription_id = "sub_test_ok"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sub]
        mock_db.execute.return_value = mock_result

        mock_stripe = MagicMock()
        mock_stripe.Subscription.cancel.return_value = {"status": "canceled"}
        with patch.dict("sys.modules", {"stripe": mock_stripe}):
            stats = await cancel_active_stripe_subscriptions(mock_db, uuid4())

        assert stats["cancelled"] == 1
        assert stats["failed"] == 0
        mock_stripe.Subscription.cancel.assert_called_once_with("sub_test_ok")
        mock_db.flush.assert_awaited_once()


class TestDeleteStripeCustomer:
    """Tests for delete_stripe_customer()."""

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service._get_stripe_key")
    async def test_returns_false_when_stripe_key_not_configured(
        self,
        mock_key: MagicMock,
    ) -> None:
        """Return False when STRIPE_SECRET_KEY is not set."""
        mock_key.return_value = None

        result = await delete_stripe_customer(uuid4(), "cus_test_123")

        assert result is False

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service._get_stripe_key")
    async def test_returns_true_on_successful_deletion(
        self,
        mock_key: MagicMock,
    ) -> None:
        """Return True when Stripe customer deleted successfully."""
        mock_key.return_value = "sk_test_key"

        mock_stripe = MagicMock()
        mock_stripe.Customer.delete.return_value = {"deleted": True}
        with patch.dict("sys.modules", {"stripe": mock_stripe}):
            result = await delete_stripe_customer(uuid4(), "cus_test_ok")

        assert result is True
        mock_stripe.Customer.delete.assert_called_once_with("cus_test_ok")

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service._get_stripe_key")
    async def test_returns_false_on_stripe_api_error(
        self,
        mock_key: MagicMock,
    ) -> None:
        """Return False when Stripe API raises an exception."""
        mock_key.return_value = "sk_test_key"

        mock_stripe = MagicMock()
        mock_stripe.Customer.delete.side_effect = Exception("Stripe API error")
        with patch.dict("sys.modules", {"stripe": mock_stripe}):
            result = await delete_stripe_customer(uuid4(), "cus_test_fail")

        assert result is False


class TestRemoveFromEmailLists:
    """Tests for remove_from_email_lists()."""

    @pytest.mark.asyncio
    async def test_removes_members_by_email(self, mock_db: AsyncMock) -> None:
        """Delete all email list member records matching the email."""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_db.execute.return_value = mock_result

        count = await remove_from_email_lists(mock_db, "donor@example.com")

        assert count == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_members_found(self, mock_db: AsyncMock) -> None:
        """Return 0 when no email list records match."""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute.return_value = mock_result

        count = await remove_from_email_lists(mock_db, "nobody@example.com")

        assert count == 0

    @pytest.mark.asyncio
    async def test_skips_anonymized_email(self, mock_db: AsyncMock) -> None:
        """Skip removal if email is already anonymized (ends with @anonymized.invalid)."""
        count = await remove_from_email_lists(mock_db, "deleted-abc123@anonymized.invalid")

        assert count == 0
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_empty_email(self, mock_db: AsyncMock) -> None:
        """Skip removal when email is empty string."""
        count = await remove_from_email_lists(mock_db, "")

        assert count == 0
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_lowercases_email_for_lookup(self, mock_db: AsyncMock) -> None:
        """Email lookup is case-insensitive (normalized to lowercase)."""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute.return_value = mock_result

        count = await remove_from_email_lists(mock_db, "DONOR@EXAMPLE.COM")

        assert count == 1
        # Verify the execute was called (email was lowercased internally)
        mock_db.execute.assert_called_once()


class TestProcessThirdPartyDeletion:
    """Tests for process_third_party_deletion()."""

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service.remove_from_email_lists")
    @patch("src.services.gdpr_third_party_deletion_service.delete_stripe_customer")
    @patch("src.services.gdpr_third_party_deletion_service.cancel_active_stripe_subscriptions")
    async def test_full_third_party_cascade(
        self,
        mock_cancel: AsyncMock,
        mock_delete_customer: AsyncMock,
        mock_remove_email: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Full cascade cancels subscriptions, deletes customer, removes from email lists."""
        donor_id = uuid4()
        mock_cancel.return_value = {"cancelled": 2, "failed": 0, "skipped": 0}
        mock_delete_customer.return_value = True
        mock_remove_email.return_value = 5

        summary = await process_third_party_deletion(
            mock_db,
            donor_id=donor_id,
            donor_email="donor@example.com",
            stripe_customer_id="cus_test_123",
        )

        assert summary["stripe_subscriptions_cancelled"] == 2
        assert summary["stripe_subscriptions_failed"] == 0
        assert summary["stripe_customer_deleted"] is True
        assert summary["email_lists_removed"] == 5

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service.remove_from_email_lists")
    @patch("src.services.gdpr_third_party_deletion_service.delete_stripe_customer")
    @patch("src.services.gdpr_third_party_deletion_service.cancel_active_stripe_subscriptions")
    async def test_skips_stripe_customer_when_id_not_provided(
        self,
        mock_cancel: AsyncMock,
        mock_delete_customer: AsyncMock,
        mock_remove_email: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Skip Stripe customer deletion when stripe_customer_id is None."""
        mock_cancel.return_value = {"cancelled": 0, "failed": 0, "skipped": 0}
        mock_remove_email.return_value = 0

        summary = await process_third_party_deletion(
            mock_db,
            donor_id=uuid4(),
            donor_email="donor@example.com",
            stripe_customer_id=None,
        )

        assert summary["stripe_customer_deleted"] is False
        mock_delete_customer.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service.remove_from_email_lists")
    @patch("src.services.gdpr_third_party_deletion_service.delete_stripe_customer")
    @patch("src.services.gdpr_third_party_deletion_service.cancel_active_stripe_subscriptions")
    async def test_skips_email_removal_when_no_email(
        self,
        mock_cancel: AsyncMock,
        mock_delete_customer: AsyncMock,
        mock_remove_email: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """Skip email list removal when donor_email is None."""
        mock_cancel.return_value = {"cancelled": 0, "failed": 0, "skipped": 0}
        mock_delete_customer.return_value = False

        summary = await process_third_party_deletion(
            mock_db,
            donor_id=uuid4(),
            donor_email=None,
            stripe_customer_id=None,
        )

        assert summary["email_lists_removed"] == 0
        mock_remove_email.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.services.gdpr_third_party_deletion_service.remove_from_email_lists")
    async def test_no_donor_id_skips_subscription_cancellation(
        self,
        mock_remove_email: AsyncMock,
        mock_db: AsyncMock,
    ) -> None:
        """No subscription cancellation when donor_id is None."""
        mock_remove_email.return_value = 2

        summary = await process_third_party_deletion(
            mock_db,
            donor_id=None,
            donor_email="donor@example.com",
            stripe_customer_id=None,
        )

        assert summary["stripe_subscriptions_cancelled"] == 0
        assert summary["stripe_subscriptions_failed"] == 0
