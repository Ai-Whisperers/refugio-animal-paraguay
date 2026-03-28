"""Unit tests for the batch receipt generation and email service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.annual_donation_summary_service import DonationLineItem
from src.services.batch_receipt_service import (
    BatchReceiptResult,
    BatchReceiptService,
    DonorReceiptInput,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_settings(smtp_enabled: bool = False) -> MagicMock:
    """Return a mock Settings object."""
    s = MagicMock()
    s.smtp_enabled = smtp_enabled
    s.smtp_host = "localhost"
    s.smtp_port = 587
    s.smtp_username = ""
    s.smtp_password = ""
    s.smtp_use_tls = True
    s.email_from_address = "noreply@refugioanimalparaguay.org"
    s.email_from_name = "Refugio Animal Paraguay"
    return s


def _make_donor(
    *,
    donor_email: str | None = "donor@example.nl",
    num_donations: int = 2,
) -> DonorReceiptInput:
    donations = [
        DonationLineItem(
            donation_id=uuid4(),
            date=datetime(2025, i + 1, 1, tzinfo=UTC),
            amount_cents=5000,
            currency="EUR",
            payment_method="stripe",
            fund_category="medical",
            receipt_number=f"REC-{i:03d}",
        )
        for i in range(num_donations)
    ]
    return DonorReceiptInput(
        donor_id=uuid4(),
        donor_name="Jan de Vries",
        donor_email=donor_email,
        donor_country="NL",
        donations=donations,
        totals_by_currency={"EUR": 5000 * num_donations},
    )


@pytest.fixture
def service_dry_run() -> BatchReceiptService:
    """Service with SMTP disabled (dry-run mode)."""
    return BatchReceiptService(_make_settings(smtp_enabled=False))


@pytest.fixture
def service_smtp_enabled() -> BatchReceiptService:
    """Service with SMTP enabled."""
    return BatchReceiptService(_make_settings(smtp_enabled=True))


# ---------------------------------------------------------------------------
# BatchReceiptResult
# ---------------------------------------------------------------------------


class TestBatchReceiptResult:
    def test_success_true_when_no_failures(self) -> None:
        r = BatchReceiptResult(year=2025, sent=3)
        assert r.success is True

    def test_success_false_when_failures(self) -> None:
        r = BatchReceiptResult(year=2025, failed=1)
        assert r.success is False

    def test_errors_default_empty(self) -> None:
        r = BatchReceiptResult(year=2025)
        assert r.errors == []

    def test_started_at_set_automatically(self) -> None:
        r = BatchReceiptResult(year=2025)
        assert r.started_at is not None


# ---------------------------------------------------------------------------
# BatchReceiptService.run — dry-run (smtp_enabled=False)
# ---------------------------------------------------------------------------


class TestRunDryRun:
    @pytest.mark.asyncio
    async def test_empty_donor_list(self, service_dry_run: BatchReceiptService) -> None:
        result = await service_dry_run.run(year=2025, donors=[])
        assert result.total_donors == 0
        assert result.sent == 0
        assert result.dry_run_would_send == 0
        assert result.failed == 0
        assert result.finished_at is not None

    @pytest.mark.asyncio
    async def test_single_donor_dry_run(self, service_dry_run: BatchReceiptService) -> None:
        donor = _make_donor()
        result = await service_dry_run.run(year=2025, donors=[donor])
        assert result.total_donors == 1
        assert result.dry_run_would_send == 1
        assert result.sent == 0
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_multiple_donors_dry_run(self, service_dry_run: BatchReceiptService) -> None:
        donors = [_make_donor() for _ in range(5)]
        result = await service_dry_run.run(year=2025, donors=donors)
        assert result.total_donors == 5
        assert result.dry_run_would_send == 5
        assert result.sent == 0

    @pytest.mark.asyncio
    async def test_donor_without_email_skipped(self, service_dry_run: BatchReceiptService) -> None:
        donors = [
            _make_donor(donor_email=None),
            _make_donor(),
        ]
        result = await service_dry_run.run(year=2025, donors=donors)
        assert result.skipped_no_email == 1
        assert result.dry_run_would_send == 1

    @pytest.mark.asyncio
    async def test_result_has_correct_year(self, service_dry_run: BatchReceiptService) -> None:
        result = await service_dry_run.run(year=2024, donors=[])
        assert result.year == 2024


# ---------------------------------------------------------------------------
# BatchReceiptService.run — SMTP enabled path
# ---------------------------------------------------------------------------


class TestRunSmtpEnabled:
    @pytest.mark.asyncio
    async def test_successful_send_increments_sent(
        self, service_smtp_enabled: BatchReceiptService
    ) -> None:
        donor = _make_donor()
        with patch(
            "src.services.batch_receipt_service.aiosmtplib.send",
            new_callable=AsyncMock,
        ):
            result = await service_smtp_enabled.run(year=2025, donors=[donor])
        assert result.sent == 1
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_smtp_failure_increments_failed(
        self, service_smtp_enabled: BatchReceiptService
    ) -> None:
        import aiosmtplib

        donor = _make_donor()
        with patch(
            "src.services.batch_receipt_service.aiosmtplib.send",
            side_effect=aiosmtplib.SMTPException("connection refused"),
        ):
            result = await service_smtp_enabled.run(year=2025, donors=[donor])
        assert result.failed == 1
        assert result.sent == 0
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_partial_failure_tracks_correctly(
        self, service_smtp_enabled: BatchReceiptService
    ) -> None:
        import aiosmtplib

        donors = [_make_donor() for _ in range(3)]
        call_count = 0

        async def smtp_side_effect(*args: object, **kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise aiosmtplib.SMTPException("temporary failure")

        with patch(
            "src.services.batch_receipt_service.aiosmtplib.send",
            side_effect=smtp_side_effect,
        ):
            result = await service_smtp_enabled.run(year=2025, donors=donors)
        assert result.sent == 2
        assert result.failed == 1

    @pytest.mark.asyncio
    async def test_success_false_on_any_failure(
        self, service_smtp_enabled: BatchReceiptService
    ) -> None:
        import aiosmtplib

        donors = [_make_donor()]
        with patch(
            "src.services.batch_receipt_service.aiosmtplib.send",
            side_effect=aiosmtplib.SMTPException("timeout"),
        ):
            result = await service_smtp_enabled.run(year=2025, donors=donors)
        assert result.success is False
