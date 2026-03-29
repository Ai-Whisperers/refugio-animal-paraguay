"""Donation receipt PDF generation service.

Generates Spanish-language donation receipts using fpdf2 with shelter info,
donation details, and tax-relevant data. Receipts can be returned as bytes
for streaming or saved to the filesystem.

Uses the centralized :class:`~src.services.pdf_service.BasePDFGenerator` and
:class:`~src.services.pdf_service.ShelterPDF` for consistent shelter branding.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.services.pdf_service import BasePDFGenerator, ShelterPDF

logger = logging.getLogger(__name__)

CURRENCY_SYMBOLS: dict[str, str] = {
    "EUR": "EUR",
    "USD": "USD",
    "PYG": "PYG",
}

PAYMENT_METHOD_LABELS: dict[str, str] = {
    "stripe": "Tarjeta (Stripe)",
    "cash": "Efectivo",
    "transfer": "Transferencia bancaria",
    "sepa_debit": "Debito directo SEPA",
    "tigo_money": "Tigo Money",
}

FUND_CATEGORY_LABELS: dict[str, str] = {
    "medical": "Atencion medica",
    "food": "Alimentacion",
    "operations": "Operaciones",
    "infrastructure": "Infraestructura",
    "emergency": "Emergencia",
}

RECEIPT_TITLE = "RECIBO DE DONACION"


@dataclass(frozen=True)
class ReceiptData:
    """Data required to render a donation receipt PDF."""

    donation_id: UUID
    amount_cents: int
    currency: str
    payment_method: str
    status: str
    receipt_number: str | None
    fund_category: str | None
    is_recurring: bool
    recurring_interval: str | None
    notes: str | None
    donation_date: datetime
    # Donor info (optional for anonymous donations)
    donor_name: str | None
    donor_email: str | None
    donor_country: str | None


def _format_amount(amount_cents: int, currency: str) -> str:
    """Format amount in cents to a human-readable string."""
    if currency == "PYG":
        # PYG has no decimal places
        return f"{amount_cents:,} {CURRENCY_SYMBOLS.get(currency, currency)}"
    amount = amount_cents / 100
    return f"{amount:,.2f} {CURRENCY_SYMBOLS.get(currency, currency)}"


class DonationReceiptGenerator(BasePDFGenerator):
    """Generates Spanish-language donation receipt PDFs using the centralized ShelterPDF base.

    Example::

        generator = DonationReceiptGenerator()
        pdf_bytes = generator.generate_bytes(receipt_data)
    """

    def _build_pdf(self, data: ReceiptData) -> ShelterPDF:  # type: ignore[override]
        """Build a branded donation receipt PDF.

        Args:
            data: :class:`ReceiptData` with donation and donor information.

        Returns:
            A fully-populated :class:`~src.services.pdf_service.ShelterPDF` instance.
        """
        pdf = ShelterPDF(title=RECEIPT_TITLE)
        pdf.add_page()

        # --- Receipt number and date ---
        pdf.section_title("Informacion del Recibo")
        pdf.info_row("No. de Recibo:", data.receipt_number or str(data.donation_id)[:12].upper())
        pdf.info_row("Fecha de Donacion:", data.donation_date.strftime("%d/%m/%Y %H:%M"))
        pdf.info_row("Fecha de Emision:", datetime.now().strftime("%d/%m/%Y %H:%M"))
        pdf.ln(4)

        # --- Donor Info ---
        pdf.section_title("Datos del Donante")
        pdf.info_row("Nombre:", data.donor_name or "Donacion anonima")
        if data.donor_email:
            pdf.info_row("Email:", data.donor_email)
        if data.donor_country:
            pdf.info_row("Pais:", data.donor_country)
        pdf.ln(4)

        # --- Donation Details ---
        pdf.section_title("Detalles de la Donacion")
        pdf.info_row("Monto:", _format_amount(data.amount_cents, data.currency))
        pdf.info_row("Moneda:", data.currency)
        pdf.info_row(
            "Metodo de Pago:",
            PAYMENT_METHOD_LABELS.get(data.payment_method, data.payment_method),
        )
        pdf.info_row("Estado:", data.status.capitalize())

        if data.is_recurring:
            interval_label = "mensual" if data.recurring_interval == "month" else "anual"
            pdf.info_row("Tipo:", f"Donacion recurrente ({interval_label})")

        if data.fund_category:
            pdf.info_row(
                "Categoria:",
                FUND_CATEGORY_LABELS.get(data.fund_category, data.fund_category),
            )

        if data.notes:
            pdf.info_row("Notas:", data.notes)
        pdf.ln(6)

        # --- Tax Notice ---
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        shelter_name = "Refugio Animal Paraguay"
        pdf.multi_cell(
            0,
            5,
            (
                "Este recibo se emite como comprobante de su generosa donacion al "
                f"{shelter_name}. Para consultas sobre deducciones fiscales, "
                "consulte con su asesor tributario. Conserve este recibo para "
                "sus registros."
            ),
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        # --- Donation ID footer ---
        pdf.divider()
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            5,
            f"ID de Donacion: {data.donation_id}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_text_color(0, 0, 0)

        logger.info(
            "Receipt PDF built for donation_id=%s",
            data.donation_id,
        )
        return pdf
