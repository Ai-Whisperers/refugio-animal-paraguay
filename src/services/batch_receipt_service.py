"""Batch tax receipt generation and email delivery service.

Generates annual donation summary PDFs for all donors with completed
donations in a given year and delivers them by email. Designed for
year-end EU donor mailings.

Design notes:
- Each donor is processed independently; failures are collected and
  returned in the result rather than aborting the batch.
- Email attachment uses Python's standard MIMEMultipart directly to
  avoid extending EmailService (which handles plain HTML only).
- smtp_enabled=False results in dry-run mode: PDFs are generated but
  not emailed; counts are reported as "would_send".
"""

import email.mime.application
import email.mime.multipart
import email.mime.text
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import aiosmtplib

from src.config import Settings
from src.services.annual_donation_summary_service import (
    AnnualDonationSummaryGenerator,
    AnnualSummaryData,
    DonationLineItem,
)

logger = logging.getLogger(__name__)

BATCH_SUBJECT_TEMPLATE = "Your {year} Donation Summary — Refugio Animal Paraguay"
BATCH_BODY_TEMPLATE = """\
<html><body>
<p>Dear {donor_name},</p>
<p>Please find attached your annual donation summary for {year} from
<strong>Refugio Animal Paraguay</strong>.</p>
<p>This document may be used to support a tax deduction claim in your
country of residence. For Dutch donors, please refer to the ANBI
information in the attachment.</p>
<p>Thank you for your generous support.</p>
<p>Refugio Animal Paraguay<br>
info@refugioanimalparaguay.org</p>
</body></html>
"""


@dataclass
class BatchReceiptResult:
    """Summary of a batch receipt generation and email run."""

    year: int
    total_donors: int = 0
    sent: int = 0
    dry_run_would_send: int = 0
    failed: int = 0
    skipped_no_email: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    @property
    def success(self) -> bool:
        """True if batch completed with zero failures."""
        return self.failed == 0


@dataclass(frozen=True)
class DonorReceiptInput:
    """Minimal donor + donation data needed to generate one receipt."""

    donor_id: UUID
    donor_name: str
    donor_email: str | None
    donor_country: str | None
    donations: list[DonationLineItem]
    totals_by_currency: dict[str, int]


class BatchReceiptService:
    """Orchestrates batch annual receipt generation and email delivery."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._generator = AnnualDonationSummaryGenerator()

    async def run(
        self,
        year: int,
        donors: list[DonorReceiptInput],
    ) -> BatchReceiptResult:
        """Generate and email annual summaries for all provided donors.

        Args:
            year: Tax year for the receipts.
            donors: List of donor input records (queried by caller).

        Returns:
            BatchReceiptResult with per-category counts and any errors.
        """
        result = BatchReceiptResult(year=year, total_donors=len(donors))

        for donor in donors:
            try:
                await self._process_one(year, donor, result)
            except Exception as exc:
                logger.exception(
                    "Unexpected error processing donor_id=%s in batch year=%d",
                    donor.donor_id,
                    year,
                )
                result.failed += 1
                result.errors.append({"donor_id": str(donor.donor_id), "error": str(exc)})

        result.finished_at = datetime.now(UTC)
        logger.info(
            "Batch receipt run complete: year=%d total=%d sent=%d dry_run=%d failed=%d skipped=%d",
            year,
            result.total_donors,
            result.sent,
            result.dry_run_would_send,
            result.failed,
            result.skipped_no_email,
        )
        return result

    async def _process_one(
        self,
        year: int,
        donor: DonorReceiptInput,
        result: BatchReceiptResult,
    ) -> None:
        """Generate a PDF and (optionally) email it for one donor."""
        if not donor.donor_email:
            logger.debug("Skipping donor_id=%s — no email address", donor.donor_id)
            result.skipped_no_email += 1
            return

        summary_data = AnnualSummaryData(
            donor_id=donor.donor_id,
            donor_name=donor.donor_name,
            donor_email=donor.donor_email,
            donor_country=donor.donor_country,
            year=year,
            donations=donor.donations,
            totals_by_currency=donor.totals_by_currency,
            generated_at=datetime.now(UTC),
        )
        pdf_bytes = self._generator.generate_bytes(summary_data)
        filename = f"donation_summary_{year}_{donor.donor_id}.pdf"

        if not self._settings.smtp_enabled:
            logger.info(
                "Dry-run: would email %d-byte PDF to %s (donor_id=%s)",
                len(pdf_bytes),
                donor.donor_email,
                donor.donor_id,
            )
            result.dry_run_would_send += 1
            return

        sent = await self._send_with_attachment(
            to_email=donor.donor_email,
            donor_name=donor.donor_name,
            year=year,
            pdf_bytes=pdf_bytes,
            filename=filename,
        )
        if sent:
            result.sent += 1
        else:
            result.failed += 1
            result.errors.append(
                {
                    "donor_id": str(donor.donor_id),
                    "error": "SMTP delivery failed",
                }
            )

    async def _send_with_attachment(
        self,
        to_email: str,
        donor_name: str,
        year: int,
        pdf_bytes: bytes,
        filename: str,
    ) -> bool:
        """Send an email with the PDF receipt as an attachment."""
        msg = email.mime.multipart.MIMEMultipart("mixed")
        msg["From"] = f"{self._settings.email_from_name} <{self._settings.email_from_address}>"
        msg["To"] = to_email
        msg["Subject"] = BATCH_SUBJECT_TEMPLATE.format(year=year)

        html_body = BATCH_BODY_TEMPLATE.format(donor_name=donor_name, year=year)
        msg.attach(email.mime.text.MIMEText(html_body, "html", "utf-8"))

        attachment = email.mime.application.MIMEApplication(pdf_bytes, _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(attachment)

        try:
            await aiosmtplib.send(
                msg,
                hostname=self._settings.smtp_host,
                port=self._settings.smtp_port,
                username=self._settings.smtp_username or None,
                password=self._settings.smtp_password or None,
                use_tls=self._settings.smtp_use_tls,
            )
            logger.info("Batch receipt sent to %s for year=%d", to_email, year)
            return True
        except (aiosmtplib.SMTPException, OSError) as exc:
            logger.error(
                "Batch receipt delivery failed: to=%s year=%d error=%s",
                to_email,
                year,
                str(exc),
            )
            return False
