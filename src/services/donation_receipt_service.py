"""Donation receipt PDF generation service.

Generates Spanish-language donation receipts using fpdf2 with shelter info,
donation details, and tax-relevant data. Receipts can be returned as bytes
for streaming or saved to the filesystem.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fpdf import FPDF

logger = logging.getLogger(__name__)

SHELTER_NAME = "Refugio Animal Paraguay"
SHELTER_ADDRESS = "Asuncion, Paraguay"
SHELTER_EMAIL = "info@refugioanimalparaguay.org"
SHELTER_PHONE = "+595 21 XXX XXXX"

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


class DonationReceiptGenerator:
    """Generates donation receipt PDFs using fpdf2."""

    def generate_bytes(self, data: ReceiptData) -> bytes:
        """Generate a PDF receipt and return its content as bytes.

        Used for streaming responses without writing to disk.
        """
        pdf = self._build_pdf(data)
        content = bytes(pdf.output())

        logger.info(
            "Receipt PDF generated for donation_id=%s (%d bytes)",
            data.donation_id,
            len(content),
        )
        return content

    def _build_pdf(self, data: ReceiptData) -> FPDF:
        """Build the PDF document in memory."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        # --- Header / Shelter Info ---
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 12, "RECIBO DE DONACION", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 7, SHELTER_NAME, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, SHELTER_ADDRESS, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0, 6, f"{SHELTER_EMAIL} | {SHELTER_PHONE}", align="C", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)

        # --- Receipt number and date ---
        self._section_title(pdf, "Informacion del Recibo")
        self._info_row(
            pdf, "No. de Recibo:", data.receipt_number or str(data.donation_id)[:12].upper()
        )
        self._info_row(
            pdf,
            "Fecha de Donacion:",
            data.donation_date.strftime("%d/%m/%Y %H:%M"),
        )
        self._info_row(
            pdf,
            "Fecha de Emision:",
            datetime.now().strftime("%d/%m/%Y %H:%M"),
        )
        pdf.ln(6)

        # --- Donor Info ---
        self._section_title(pdf, "Datos del Donante")
        if data.donor_name:
            self._info_row(pdf, "Nombre:", data.donor_name)
        else:
            self._info_row(pdf, "Nombre:", "Donacion anonima")
        if data.donor_email:
            self._info_row(pdf, "Email:", data.donor_email)
        if data.donor_country:
            self._info_row(pdf, "Pais:", data.donor_country)
        pdf.ln(6)

        # --- Donation Details ---
        self._section_title(pdf, "Detalles de la Donacion")
        self._info_row(pdf, "Monto:", _format_amount(data.amount_cents, data.currency))
        self._info_row(pdf, "Moneda:", data.currency)
        self._info_row(
            pdf,
            "Metodo de Pago:",
            PAYMENT_METHOD_LABELS.get(data.payment_method, data.payment_method),
        )
        self._info_row(pdf, "Estado:", data.status.capitalize())

        if data.is_recurring:
            interval_label = "mensual" if data.recurring_interval == "month" else "anual"
            self._info_row(pdf, "Tipo:", f"Donacion recurrente ({interval_label})")

        if data.fund_category:
            category_labels: dict[str, str] = {
                "medical": "Atencion medica",
                "food": "Alimentacion",
                "operations": "Operaciones",
                "infrastructure": "Infraestructura",
                "emergency": "Emergencia",
            }
            self._info_row(
                pdf,
                "Categoria:",
                category_labels.get(data.fund_category, data.fund_category),
            )

        if data.notes:
            self._info_row(pdf, "Notas:", data.notes)
        pdf.ln(8)

        # --- Tax Notice ---
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(
            0,
            5,
            (
                "Este recibo se emite como comprobante de su generosa donacion al "
                f"{SHELTER_NAME}. Para consultas sobre deducciones fiscales, "
                "consulte con su asesor tributario. Conserve este recibo para "
                "sus registros."
            ),
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

        # --- Footer line ---
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            5,
            f"Documento generado automaticamente - {SHELTER_NAME}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            5,
            f"ID de Donacion: {data.donation_id}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        return pdf

    @staticmethod
    def _section_title(pdf: FPDF, title: str) -> None:
        """Render a section title with a bottom border."""
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)

    @staticmethod
    def _info_row(pdf: FPDF, label: str, value: str) -> None:
        """Render a label: value row."""
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(55, 6, label)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")
