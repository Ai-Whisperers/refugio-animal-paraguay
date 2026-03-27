"""Unit tests for the dunning notification service.

Tests tiered email sending based on failed payment counts.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.dunning_service import (
    SUBJECT_FINAL_NOTICE,
    SUBJECT_FIRST_NOTICE,
    SUBJECT_SECOND_NOTICE,
    TEMPLATE_FINAL_NOTICE,
    TEMPLATE_FIRST_NOTICE,
    TEMPLATE_SECOND_NOTICE,
    DunningService,
    _format_amount,
    _format_interval_label,
)


class TestFormatHelpers:
    """Tests for dunning format helper functions."""

    def test_format_interval_label_month(self) -> None:
        assert _format_interval_label("month") == "monthly"

    def test_format_interval_label_year(self) -> None:
        assert _format_interval_label("year") == "yearly"

    def test_format_interval_label_unknown(self) -> None:
        assert _format_interval_label("week") == "week"

    def test_format_amount_eur(self) -> None:
        assert _format_amount(1500, "EUR") == "15.00"

    def test_format_amount_pyg(self) -> None:
        assert _format_amount(500000, "PYG") == "5,000"

    def test_format_amount_usd(self) -> None:
        assert _format_amount(2550, "USD") == "25.50"


class TestDunningService:
    """Tests for DunningService.send_dunning_email."""

    def _make_subscription(self) -> MagicMock:
        sub = MagicMock()
        sub.id = uuid4()
        sub.donor_id = uuid4()
        sub.amount_cents = 2000
        sub.currency = "EUR"
        sub.interval = "month"
        return sub

    def _make_donor(self) -> MagicMock:
        donor = MagicMock()
        donor.id = uuid4()
        donor.full_name = "Jan de Vries"
        donor.email = "jan@example.nl"
        return donor

    def _make_service(self) -> tuple[DunningService, AsyncMock, MagicMock]:
        email_service = AsyncMock()
        renderer = MagicMock()
        renderer.render.return_value = "<html>dunning</html>"
        service = DunningService(email_service, renderer, max_attempts=3)
        return service, email_service, renderer

    @pytest.mark.asyncio
    async def test_sends_first_notice_on_first_failure(self) -> None:
        service, email_mock, renderer_mock = self._make_service()
        donor = self._make_donor()
        subscription = self._make_subscription()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            return_value=(donor, subscription),
        ):
            result = await service.send_dunning_email(
                subscription_id=subscription.id,
                failed_count=1,
                error_message="Card declined",
            )

        assert result == "first_notice_sent"
        renderer_mock.render.assert_called_once()
        template_name = renderer_mock.render.call_args[0][0]
        assert template_name == TEMPLATE_FIRST_NOTICE
        email_mock.send_email.assert_called_once()
        sent_message = email_mock.send_email.call_args[0][0]
        assert sent_message.subject == SUBJECT_FIRST_NOTICE
        assert sent_message.to == donor.email

    @pytest.mark.asyncio
    async def test_sends_second_notice_on_second_failure(self) -> None:
        service, email_mock, renderer_mock = self._make_service()
        donor = self._make_donor()
        subscription = self._make_subscription()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            return_value=(donor, subscription),
        ):
            result = await service.send_dunning_email(
                subscription_id=subscription.id,
                failed_count=2,
                error_message="Insufficient funds",
            )

        assert result == "second_notice_sent"
        template_name = renderer_mock.render.call_args[0][0]
        assert template_name == TEMPLATE_SECOND_NOTICE
        sent_message = email_mock.send_email.call_args[0][0]
        assert sent_message.subject == SUBJECT_SECOND_NOTICE

    @pytest.mark.asyncio
    async def test_sends_final_notice_on_max_failures(self) -> None:
        service, email_mock, renderer_mock = self._make_service()
        donor = self._make_donor()
        subscription = self._make_subscription()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            return_value=(donor, subscription),
        ):
            result = await service.send_dunning_email(
                subscription_id=subscription.id,
                failed_count=3,
                error_message="Card expired",
            )

        assert result == "final_notice_sent"
        template_name = renderer_mock.render.call_args[0][0]
        assert template_name == TEMPLATE_FINAL_NOTICE
        sent_message = email_mock.send_email.call_args[0][0]
        assert sent_message.subject == SUBJECT_FINAL_NOTICE

    @pytest.mark.asyncio
    async def test_sends_final_notice_when_exceeds_max(self) -> None:
        """Even above max_attempts, send final notice (not second)."""
        service, _email_mock, _renderer_mock = self._make_service()
        donor = self._make_donor()
        subscription = self._make_subscription()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            return_value=(donor, subscription),
        ):
            result = await service.send_dunning_email(
                subscription_id=subscription.id,
                failed_count=5,
            )

        assert result == "final_notice_sent"

    @pytest.mark.asyncio
    async def test_skips_when_donor_not_found(self) -> None:
        service, email_mock, _ = self._make_service()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            return_value=(None, None),
        ):
            result = await service.send_dunning_email(
                subscription_id=uuid4(),
                failed_count=1,
            )

        assert result == "dunning_skipped"
        email_mock.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_subscription_not_found(self) -> None:
        service, email_mock, _ = self._make_service()
        donor = self._make_donor()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            return_value=(donor, None),
        ):
            result = await service.send_dunning_email(
                subscription_id=uuid4(),
                failed_count=1,
            )

        assert result == "dunning_skipped"
        email_mock.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self) -> None:
        service, _, _ = self._make_service()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB connection lost"),
        ):
            result = await service.send_dunning_email(
                subscription_id=uuid4(),
                failed_count=1,
            )

        assert result == "dunning_error"

    @pytest.mark.asyncio
    async def test_template_context_includes_required_fields(self) -> None:
        """Verify the context dict passed to the template renderer."""
        service, _, renderer_mock = self._make_service()
        donor = self._make_donor()
        subscription = self._make_subscription()

        with patch.object(
            DunningService,
            "_lookup_subscription_and_donor",
            new_callable=AsyncMock,
            return_value=(donor, subscription),
        ):
            await service.send_dunning_email(
                subscription_id=subscription.id,
                failed_count=1,
                error_message="Declined",
            )

        context = renderer_mock.render.call_args[0][1]
        assert context["donor_name"] == "Jan de Vries"
        assert context["amount"] == "20.00"
        assert context["currency"] == "EUR"
        assert context["interval_label"] == "monthly"
        assert context["error_message"] == "Declined"
        assert context["attempt_number"] == 1
        assert context["max_attempts"] == 3
        assert "support_email" in context
