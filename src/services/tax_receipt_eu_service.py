"""EU-format tax receipt PDF generation service.

Generates bilingual (Dutch/Spanish) tax receipts for European donors in
compliance with Dutch ANBI (Algemeen Nut Beogende Instelling) requirements.
Receipts include all fields required for Dutch tax deductibility claims.
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

# Dutch ANBI registration - to be updated with actual RSIN when registered
SHELTER_ANBI_RSIN = "RSIN: PENDING REGISTRATION"
SHELTER_KVKNR = "KvK: N/A (foreign charity)"

CURRENCY_SYMBOLS: dict[str, str] = {
    "EUR": "EUR",
    "USD": "USD",
    "PYG": "PYG",
}

PAYMENT_METHOD_LABELS: dict[str, str] = {
    "stripe": "Card / Kaart (Stripe)",
    "cash": "Cash / Efectivo",
    "transfer": "Bank transfer / Overschrijving",
    "sepa_debit": "SEPA Direct Debit",
    "tigo_money": "Tigo Money",
}


@dataclass(frozen=True)
class EUReceiptData:
    """Data required to render an EU-format tax receipt PDF."""

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
    # Donor info - name is required for EU tax deductibility
    donor_name: str | None
    donor_email: str | None
    donor_country: str | None
    # EU-specific: tax ID (BSN for Dutch donors, TIN for other EU)
    donor_tax_id: str | None = None


def _format_amount(amount_cents: int, currency: str) -> str:
    """Format amount in cents to a human-readable string."""
    if currency == "PYG":
        return f"{amount_cents:,} {CURRENCY_SYMBOLS.get(currency, currency)}"
    amount = amount_cents / 100
    return f"{amount:,.2f} {CURRENCY_SYMBOLS.get(currency, currency)}"


class TaxReceiptEUGenerator:
    """Generates EU-format (Dutch ANBI compliant) donation receipt PDFs using fpdf2."""

    def generate_bytes(self, data: EUReceiptData) -> bytes:
        """Generate a PDF receipt and return its content as bytes.

        Used for streaming responses without writing to disk.
        """
        pdf = self._build_pdf(data)
        content = bytes(pdf.output())

        logger.info(
            "EU tax receipt PDF generated for donation_id=%s (%d bytes)",
            data.donation_id,
            len(content),
        )
        return content

    def _build_pdf(self, data: EUReceiptData) -> FPDF:
        """Build the EU-format PDF document in memory."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        self._render_header(pdf)
        self._render_receipt_info(pdf, data)
        self._render_donor_info(pdf, data)
        self._render_donation_details(pdf, data)
        self._render_anbi_notice(pdf)
        self._render_footer(pdf, data)

        return pdf

    def _render_header(self, pdf: FPDF) -> None:
        """Render shelter header with ANBI identification."""
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(
            0,
            10,
            "DONATION TAX RECEIPT / KWITANTIE BELASTINGAFTREK",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 7, SHELTER_NAME, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, SHELTER_ADDRESS, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0,
            5,
            f"{SHELTER_EMAIL} | {SHELTER_PHONE}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            5,
            f"{SHELTER_ANBI_RSIN} | {SHELTER_KVKNR}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)

        pdf.set_draw_color(60, 120, 180)
        pdf.set_line_width(0.5)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(6)

    def _render_receipt_info(self, pdf: FPDF, data: EUReceiptData) -> None:
        """Render receipt number and dates."""
        self._section_title(pdf, "Receipt Information / Ontvangstbewijs")
        self._bilingual_row(
            pdf,
            "Receipt No. / Nr.:",
            data.receipt_number or str(data.donation_id)[:12].upper(),
        )
        self._bilingual_row(
            pdf,
            "Donation Date / Datum donatie:",
            data.donation_date.strftime("%d/%m/%Y"),
        )
        self._bilingual_row(
            pdf,
            "Issue Date / Datum uitgifte:",
            datetime.now().strftime("%d/%m/%Y"),
        )
        pdf.ln(6)

    def _render_donor_info(self, pdf: FPDF, data: EUReceiptData) -> None:
        """Render donor identification section."""
        self._section_title(pdf, "Donor / Donateur")
        donor_name = data.donor_name or "Anonymous / Anoniem"
        self._bilingual_row(pdf, "Name / Naam:", donor_name)

        if data.donor_email:
            self._bilingual_row(pdf, "Email:", data.donor_email)

        if data.donor_country:
            self._bilingual_row(pdf, "Country / Land:", data.donor_country)

        if data.donor_tax_id:
            self._bilingual_row(pdf, "Tax ID / BSN/TIN:", data.donor_tax_id)

        pdf.ln(6)

    def _render_donation_details(self, pdf: FPDF, data: EUReceiptData) -> None:
        """Render donation amount and payment details."""
        self._section_title(pdf, "Donation Details / Donatie Details")
        self._bilingual_row(
            pdf,
            "Amount / Bedrag:",
            _format_amount(data.amount_cents, data.currency),
        )
        self._bilingual_row(pdf, "Currency / Valuta:", data.currency)
        self._bilingual_row(
            pdf,
            "Payment Method / Betaalmethode:",
            PAYMENT_METHOD_LABELS.get(data.payment_method, data.payment_method),
        )
        self._bilingual_row(pdf, "Status:", data.status.capitalize())

        if data.is_recurring:
            interval_en = "monthly" if data.recurring_interval == "month" else "annual"
            interval_nl = "maandelijks" if data.recurring_interval == "month" else "jaarlijks"
            self._bilingual_row(
                pdf,
                "Type:",
                f"Recurring donation ({interval_en}) / Periodieke gift ({interval_nl})",
            )

        if data.fund_category:
            category_map: dict[str, tuple[str, str]] = {
                "medical": ("Medical care", "Medische zorg"),
                "food": ("Food", "Voedsel"),
                "operations": ("Operations", "Exploitatie"),
                "infrastructure": ("Infrastructure", "Infrastructuur"),
                "emergency": ("Emergency", "Noodgeval"),
            }
            en_label, nl_label = category_map.get(
                data.fund_category, (data.fund_category, data.fund_category)
            )
            self._bilingual_row(pdf, "Purpose / Doel:", f"{en_label} / {nl_label}")

        if data.notes:
            self._bilingual_row(pdf, "Notes / Opmerkingen:", data.notes)

        pdf.ln(8)

    def _render_anbi_notice(self, pdf: FPDF) -> None:
        """Render the ANBI tax deductibility notice (required for Dutch donors)."""
        pdf.set_fill_color(240, 247, 255)
        pdf.set_draw_color(60, 120, 180)
        box_y = pdf.get_y()
        pdf.rect(pdf.l_margin, box_y, pdf.w - pdf.l_margin - pdf.r_margin, 42, style="FD")
        pdf.set_y(box_y + 3)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 80, 150)
        pdf.cell(
            0,
            5,
            "Tax Deductibility Notice (Dutch donors) / Belastingaftrek (Nederlandse donateurs)",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(
            0,
            4,
            "EN: This receipt documents a charitable gift to Refugio Animal Paraguay. "
            "Donations to foreign charitable organizations may be tax-deductible in the "
            "Netherlands if certain conditions are met. Consult your tax advisor or the "
            "Belastingdienst (belastingdienst.nl) regarding your specific situation.",
        )
        pdf.ln(2)
        pdf.multi_cell(
            0,
            4,
            "NL: Dit bewijs documenteert een gift aan Refugio Animal Paraguay. Giften aan "
            "buitenlandse goede doelen kunnen in Nederland aftrekbaar zijn als aan bepaalde "
            "voorwaarden wordt voldaan. Raadpleeg uw belastingadviseur of de Belastingdienst "
            "(belastingdienst.nl) voor uw specifieke situatie.",
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

    def _render_footer(self, pdf: FPDF, data: EUReceiptData) -> None:
        """Render document footer with donation ID."""
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)

        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            4,
            f"Auto-generated document / Automatisch gegenereerd document - {SHELTER_NAME}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            4,
            f"Donation ID / Donatie ID: {data.donation_id}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    @staticmethod
    def _section_title(pdf: FPDF, title: str) -> None:
        """Render a section title with a bottom border."""
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    @staticmethod
    def _bilingual_row(pdf: FPDF, label: str, value: str) -> None:
        """Render a label: value row."""
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(65, 5, label)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")
