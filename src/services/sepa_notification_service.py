"""SEPA-specific donor notification service.

Sends email notifications to donors for SEPA Direct Debit lifecycle events:
  - Mandate saved  (setup_intent.succeeded)
  - Payment processing  (payment_intent.processing — async 1-3 day settlement)
  - Payment failed  (payment_intent.payment_failed for SEPA payments)
  - Mandate setup failed  (setup_intent.setup_failed)

All notification methods are fire-and-forget: errors are logged but never
re-raised so that a failed notification does not block webhook processing.
"""

import logging
from uuid import UUID

from sqlalchemy import select

from src.db.models.donation import Donation, Donor
from src.db.session import get_async_session
from src.notifications.service import EmailMessage, EmailService
from src.notifications.templates import TemplateRenderer

logger = logging.getLogger(__name__)

SEPA_SUPPORT_EMAIL = "info@refugioanimalparaguay.org"


class SepaNotificationService:
    """Sends SEPA-lifecycle email notifications to donors.

    Constructed once at application startup and stored on ``app.state`` so
    webhook handlers can retrieve it without a dependency injection cycle.
    """

    def __init__(self, email_service: EmailService, renderer: TemplateRenderer) -> None:
        self._email = email_service
        self._renderer = renderer

    # ------------------------------------------------------------------
    # Public notification methods
    # ------------------------------------------------------------------

    async def notify_mandate_saved(self, donor_id: str | UUID) -> None:
        """Notify donor that their SEPA mandate has been saved.

        Called after ``setup_intent.succeeded``. The mandate allows future
        off-session charges without the donor entering their IBAN again.
        """
        try:
            donor = await self._lookup_donor(donor_id)
            if donor is None:
                logger.warning(
                    "sepa_notify: mandate_saved — donor %s not found, skipping email",
                    donor_id,
                )
                return

            html = self._renderer.render(
                "sepa_mandate_saved",
                {
                    "donor_name": donor.full_name,
                    "support_email": SEPA_SUPPORT_EMAIL,
                },
            )
            await self._email.send_email(
                EmailMessage(
                    to=donor.email,
                    subject="Your SEPA Direct Debit mandate has been set up",
                    html_body=html,
                )
            )
            logger.info("sepa_notify: mandate_saved email sent to donor %s", donor_id)
        except Exception as exc:
            logger.exception(
                "sepa_notify: failed to send mandate_saved email for donor %s: %s",
                donor_id,
                exc,
            )

    async def notify_payment_processing(self, donation_id: UUID) -> None:
        """Notify donor that their SEPA payment has been initiated.

        Called after ``payment_intent.processing``. SEPA settlement is
        asynchronous — the bank accepts the debit instruction but actual
        funds transfer takes 1-3 business days.
        """
        try:
            donor, donation = await self._lookup_donation_and_donor(donation_id)
            if donor is None or donation is None:
                logger.warning(
                    "sepa_notify: payment_processing — donation/donor not found for %s, skipping",
                    donation_id,
                )
                return

            amount_display = f"{donation.amount_cents / 100:.2f}"
            html = self._renderer.render(
                "sepa_payment_processing",
                {
                    "donor_name": donor.full_name,
                    "amount": amount_display,
                    "currency": donation.currency,
                    "support_email": SEPA_SUPPORT_EMAIL,
                },
            )
            await self._email.send_email(
                EmailMessage(
                    to=donor.email,
                    subject="Your SEPA donation is being processed",
                    html_body=html,
                )
            )
            logger.info("sepa_notify: payment_processing email sent for donation %s", donation_id)
        except Exception as exc:
            logger.exception(
                "sepa_notify: failed to send payment_processing email for donation %s: %s",
                donation_id,
                exc,
            )

    async def notify_payment_failed(
        self,
        donation_id: UUID | None = None,
        donor_id: str | UUID | None = None,
    ) -> None:
        """Notify donor that a SEPA payment has failed.

        Called after ``payment_intent.payment_failed`` (pass donation_id) or
        ``setup_intent.setup_failed`` (pass donor_id when no donation exists yet).
        At least one of the two identifiers must be provided.
        """
        try:
            donor: Donor | None = None
            amount_display: str | None = None
            currency: str | None = None

            if donation_id is not None:
                donor, donation = await self._lookup_donation_and_donor(donation_id)
                if donation is not None:
                    amount_display = f"{donation.amount_cents / 100:.2f}"
                    currency = donation.currency
            elif donor_id is not None:
                donor = await self._lookup_donor(donor_id)

            if donor is None:
                logger.warning(
                    "sepa_notify: payment_failed — could not resolve donor "
                    "(donation_id=%s, donor_id=%s), skipping email",
                    donation_id,
                    donor_id,
                )
                return

            html = self._renderer.render(
                "sepa_payment_failed",
                {
                    "donor_name": donor.full_name,
                    "amount": amount_display,
                    "currency": currency,
                    "support_email": SEPA_SUPPORT_EMAIL,
                },
            )
            await self._email.send_email(
                EmailMessage(
                    to=donor.email,
                    subject="Action required: Your SEPA donation could not be processed",
                    html_body=html,
                )
            )
            logger.info(
                "sepa_notify: payment_failed email sent (donation=%s, donor=%s)",
                donation_id,
                donor_id,
            )
        except Exception as exc:
            logger.exception(
                "sepa_notify: failed to send payment_failed email "
                "(donation_id=%s, donor_id=%s): %s",
                donation_id,
                donor_id,
                exc,
            )

    # ------------------------------------------------------------------
    # Private DB helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _lookup_donor(donor_id: str | UUID) -> "Donor | None":
        """Fetch a Donor record by ID (accepts str or UUID)."""
        try:
            uid = UUID(str(donor_id)) if not isinstance(donor_id, UUID) else donor_id
            async with get_async_session() as session:
                result = await session.execute(select(Donor).where(Donor.id == uid))
                return result.scalar_one_or_none()
        except Exception as exc:
            logger.exception("sepa_notify: DB lookup failed for donor %s: %s", donor_id, exc)
            return None

    @staticmethod
    async def _lookup_donation_and_donor(
        donation_id: UUID,
    ) -> "tuple[Donor | None, Donation | None]":
        """Fetch a Donation and its associated Donor in one session."""
        try:
            async with get_async_session() as session:
                result = await session.execute(select(Donation).where(Donation.id == donation_id))
                donation = result.scalar_one_or_none()
                if donation is None:
                    return None, None

                if donation.donor_id is None:
                    return None, donation

                donor_result = await session.execute(
                    select(Donor).where(Donor.id == donation.donor_id)
                )
                donor = donor_result.scalar_one_or_none()
                return donor, donation
        except Exception as exc:
            logger.exception("sepa_notify: DB lookup failed for donation %s: %s", donation_id, exc)
            return None, None
