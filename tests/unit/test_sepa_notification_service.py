"""Unit tests for SepaNotificationService.

Tests cover:
  - notify_mandate_saved: happy path, donor not found, exception handling
  - notify_payment_processing: happy path, donation/donor not found, exception
  - notify_payment_failed: via donation_id, via donor_id, neither provided
  - Graceful degradation: exceptions never propagate to callers
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.notifications.service import EmailService
from src.notifications.templates import TemplateRenderer
from src.services.sepa_notification_service import SepaNotificationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service() -> tuple[SepaNotificationService, MagicMock, MagicMock]:
    """Construct a SepaNotificationService with mocked dependencies."""
    email_service = MagicMock(spec=EmailService)
    email_service.send_email = AsyncMock(return_value=True)
    renderer = MagicMock(spec=TemplateRenderer)
    renderer.render.return_value = "<html>test</html>"
    service = SepaNotificationService(email_service, renderer)
    return service, email_service, renderer


def _make_donor(donor_id=None, email="donor@example.com", full_name="Maria García"):
    """Create a mock Donor ORM object."""
    donor = MagicMock()
    donor.id = donor_id or uuid4()
    donor.email = email
    donor.full_name = full_name
    return donor


def _make_donation(donation_id=None, donor_id=None, amount_cents=5000, currency="EUR"):
    """Create a mock Donation ORM object."""
    donation = MagicMock()
    donation.id = donation_id or uuid4()
    donation.donor_id = donor_id or uuid4()
    donation.amount_cents = amount_cents
    donation.currency = currency
    return donation


def _mock_lookup_donor(donor_or_none):
    """Return an async patcher for SepaNotificationService._lookup_donor."""
    return patch.object(
        SepaNotificationService,
        "_lookup_donor",
        new=AsyncMock(return_value=donor_or_none),
    )


def _mock_lookup_donation_and_donor(donor_or_none, donation_or_none):
    """Return an async patcher for _lookup_donation_and_donor."""
    return patch.object(
        SepaNotificationService,
        "_lookup_donation_and_donor",
        new=AsyncMock(return_value=(donor_or_none, donation_or_none)),
    )


# ---------------------------------------------------------------------------
# notify_mandate_saved
# ---------------------------------------------------------------------------


class TestNotifyMandateSaved:
    """Tests for SepaNotificationService.notify_mandate_saved."""

    @pytest.mark.asyncio
    async def test_sends_email_to_donor(self) -> None:
        service, email_service, renderer = _make_service()
        donor = _make_donor(email="eu@example.com", full_name="Jan Kowalski")

        with _mock_lookup_donor(donor):
            await service.notify_mandate_saved(str(donor.id))

        renderer.render.assert_called_once()
        call_args = renderer.render.call_args[0]
        assert call_args[0] == "sepa_mandate_saved"
        assert call_args[1]["donor_name"] == "Jan Kowalski"
        assert "support_email" in call_args[1]

        email_service.send_email.assert_awaited_once()
        msg = email_service.send_email.call_args[0][0]
        assert msg.to == "eu@example.com"
        assert "mandate" in msg.subject.lower()

    @pytest.mark.asyncio
    async def test_skips_when_donor_not_found(self) -> None:
        service, email_service, _ = _make_service()

        with _mock_lookup_donor(None):
            await service.notify_mandate_saved(str(uuid4()))

        email_service.send_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_email_failure(self) -> None:
        service, email_service, _ = _make_service()
        donor = _make_donor()
        email_service.send_email = AsyncMock(side_effect=Exception("SMTP down"))

        with _mock_lookup_donor(donor):
            # Must not propagate — graceful degradation
            await service.notify_mandate_saved(str(donor.id))

    @pytest.mark.asyncio
    async def test_does_not_raise_on_lookup_failure(self) -> None:
        service, email_service, _ = _make_service()

        with patch.object(
            SepaNotificationService,
            "_lookup_donor",
            new=AsyncMock(side_effect=Exception("DB error")),
        ):
            # Must not propagate
            await service.notify_mandate_saved(str(uuid4()))

        email_service.send_email.assert_not_awaited()


# ---------------------------------------------------------------------------
# notify_payment_processing
# ---------------------------------------------------------------------------


class TestNotifyPaymentProcessing:
    """Tests for SepaNotificationService.notify_payment_processing."""

    @pytest.mark.asyncio
    async def test_sends_processing_email(self) -> None:
        service, email_service, renderer = _make_service()
        donation_id = uuid4()
        donor = _make_donor(email="donor@test.com", full_name="Anna Schmidt")
        donation = _make_donation(donation_id=donation_id, amount_cents=10000, currency="EUR")

        with _mock_lookup_donation_and_donor(donor, donation):
            await service.notify_payment_processing(donation_id)

        renderer.render.assert_called_once()
        call_args = renderer.render.call_args
        assert call_args[0][0] == "sepa_payment_processing"
        context = call_args[0][1]
        assert context["donor_name"] == "Anna Schmidt"
        assert context["amount"] == "100.00"
        assert context["currency"] == "EUR"

        email_service.send_email.assert_awaited_once()
        msg = email_service.send_email.call_args[0][0]
        assert msg.to == "donor@test.com"
        assert "sepa" in msg.subject.lower() or "process" in msg.subject.lower()

    @pytest.mark.asyncio
    async def test_skips_when_donation_not_found(self) -> None:
        service, email_service, _ = _make_service()

        with _mock_lookup_donation_and_donor(None, None):
            await service.notify_payment_processing(uuid4())

        email_service.send_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skips_when_donor_not_found(self) -> None:
        service, email_service, _ = _make_service()
        donation = _make_donation()

        with _mock_lookup_donation_and_donor(None, donation):
            await service.notify_payment_processing(uuid4())

        email_service.send_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_failure(self) -> None:
        service, email_service, _ = _make_service()
        email_service.send_email = AsyncMock(side_effect=Exception("timeout"))
        donor = _make_donor()
        donation = _make_donation()

        with _mock_lookup_donation_and_donor(donor, donation):
            await service.notify_payment_processing(uuid4())


# ---------------------------------------------------------------------------
# notify_payment_failed
# ---------------------------------------------------------------------------


class TestNotifyPaymentFailed:
    """Tests for SepaNotificationService.notify_payment_failed."""

    @pytest.mark.asyncio
    async def test_sends_failed_email_via_donation_id(self) -> None:
        service, email_service, renderer = _make_service()
        donation_id = uuid4()
        donor = _make_donor(email="fail@test.com", full_name="Pedro Martínez")
        donation = _make_donation(donation_id=donation_id, amount_cents=2500, currency="EUR")

        with _mock_lookup_donation_and_donor(donor, donation):
            await service.notify_payment_failed(donation_id=donation_id)

        renderer.render.assert_called_once()
        context = renderer.render.call_args[0][1]
        assert context["donor_name"] == "Pedro Martínez"
        assert context["amount"] == "25.00"
        assert context["currency"] == "EUR"

        msg = email_service.send_email.call_args[0][0]
        assert msg.to == "fail@test.com"
        assert "required" in msg.subject.lower() or "failed" in msg.subject.lower()

    @pytest.mark.asyncio
    async def test_sends_failed_email_via_donor_id(self) -> None:
        """Used for setup_intent.setup_failed where no donation exists."""
        service, email_service, renderer = _make_service()
        donor_id = str(uuid4())
        donor = _make_donor(email="setup@test.com", full_name="Sophie Dupont")

        with _mock_lookup_donor(donor):
            await service.notify_payment_failed(donor_id=donor_id)

        renderer.render.assert_called_once()
        context = renderer.render.call_args[0][1]
        assert context["donor_name"] == "Sophie Dupont"
        assert context["amount"] is None
        assert context["currency"] is None

        msg = email_service.send_email.call_args[0][0]
        assert msg.to == "setup@test.com"

    @pytest.mark.asyncio
    async def test_skips_when_neither_identifier_resolves(self) -> None:
        service, email_service, _ = _make_service()

        with (
            _mock_lookup_donation_and_donor(None, None),
            _mock_lookup_donor(None),
        ):
            await service.notify_payment_failed(donation_id=uuid4())

        email_service.send_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_does_not_raise_on_email_failure(self) -> None:
        service, email_service, _ = _make_service()
        email_service.send_email = AsyncMock(side_effect=Exception("server error"))
        donor = _make_donor()
        donation = _make_donation()

        with _mock_lookup_donation_and_donor(donor, donation):
            await service.notify_payment_failed(donation_id=uuid4())


# ---------------------------------------------------------------------------
# Template rendering: correct context keys
# ---------------------------------------------------------------------------


class TestTemplateContextKeys:
    """Verify render() is called with the expected template name and keys."""

    @pytest.mark.asyncio
    async def test_mandate_saved_template_name(self) -> None:
        service, _, renderer = _make_service()
        donor = _make_donor()

        with _mock_lookup_donor(donor):
            await service.notify_mandate_saved(str(donor.id))

        template_name = renderer.render.call_args[0][0]
        assert template_name == "sepa_mandate_saved"

    @pytest.mark.asyncio
    async def test_payment_processing_template_name(self) -> None:
        service, _, renderer = _make_service()
        donor = _make_donor()
        donation = _make_donation()

        with _mock_lookup_donation_and_donor(donor, donation):
            await service.notify_payment_processing(uuid4())

        template_name = renderer.render.call_args[0][0]
        assert template_name == "sepa_payment_processing"

    @pytest.mark.asyncio
    async def test_payment_failed_template_name(self) -> None:
        service, _, renderer = _make_service()
        donor = _make_donor()

        with _mock_lookup_donor(donor):
            await service.notify_payment_failed(donor_id=str(uuid4()))

        template_name = renderer.render.call_args[0][0]
        assert template_name == "sepa_payment_failed"
