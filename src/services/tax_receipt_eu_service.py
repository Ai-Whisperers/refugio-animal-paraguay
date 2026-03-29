"""EU-format tax receipt PDF generation service.

Generates bilingual (Dutch/Spanish) tax receipts for European donors in
compliance with Dutch ANBI (Algemeen Nut Beogende Instelling) requirements.
Receipts include all fields required for Dutch tax deductibility claims.

Uses the centralized :class:`~src.services.pdf_service.BasePDFGenerator` and
:class:`~src.services.pdf_service.ShelterPDF` for consistent shelter branding.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.services.pdf_service import BasePDFGenerator, ShelterPDF

logger = logging.getLogger(__name__)

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

EU_RECEIPT_TITLE = "DONATION TAX RECEIPT / KWITANTIE BELASTINGAFTREK"


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


class TaxReceiptEUGenerator(BasePDFGenerator):
    """Generates EU-format (Dutch ANBI compliant) donation receipt PDFs.

    Uses :class:`~src.services.pdf_service.ShelterPDF` for the standard shelter
    branded header/footer. Adds ANBI-specific identification and bilingual content.

    Example::

        generator = TaxReceiptEUGenerator()
        pdf_bytes = generator.generate_bytes(eu_receipt_data)
    """

    def _build_pdf(self, data: EUReceiptData) -> ShelterPDF:  # type: ignore[override]
        """Build an EU-format (ANBI-compliant) tax receipt PDF.

        Args:
            data: :class:`EUReceiptData` with donation, donor, and EU-specific fields.

        Returns:
            A fully-populated :class:`~src.services.pdf_service.ShelterPDF` instance.
        """
        pdf = ShelterPDF(title=EU_RECEIPT_TITLE)
        pdf.add_page()

        # ANBI identification line (below standard ShelterPDF header)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0,
            5,
            f"{SHELTER_ANBI_RSIN} | {SHELTER_KVKNR}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        # --- Receipt Info ---
        pdf.section_title("Receipt Information / Ontvangstbewijs")
        _bilingual_row(
            pdf, "Receipt No. / Nr.:", data.receipt_number or str(data.donation_id)[:12].upper()
        )
        _bilingual_row(
            pdf, "Donation Date / Datum donatie:", data.donation_date.strftime("%d/%m/%Y")
        )
        _bilingual_row(pdf, "Issue Date / Datum uitgifte:", datetime.now().strftime("%d/%m/%Y"))
        pdf.ln(4)

        # --- Donor Info ---
        pdf.section_title("Donor / Donateur")
        _bilingual_row(pdf, "Name / Naam:", data.donor_name or "Anonymous / Anoniem")
        if data.donor_email:
            _bilingual_row(pdf, "Email:", data.donor_email)
        if data.donor_country:
            _bilingual_row(pdf, "Country / Land:", data.donor_country)
        if data.donor_tax_id:
            _bilingual_row(pdf, "Tax ID / BSN/TIN:", data.donor_tax_id)
        pdf.ln(4)

        # --- Donation Details ---
        pdf.section_title("Donation Details / Donatie Details")
        _bilingual_row(pdf, "Amount / Bedrag:", _format_amount(data.amount_cents, data.currency))
        _bilingual_row(pdf, "Currency / Valuta:", data.currency)
        _bilingual_row(
            pdf,
            "Payment Method / Betaalmethode:",
            PAYMENT_METHOD_LABELS.get(data.payment_method, data.payment_method),
        )
        _bilingual_row(pdf, "Status:", data.status.capitalize())

        if data.is_recurring:
            interval_en = "monthly" if data.recurring_interval == "month" else "annual"
            interval_nl = "maandelijks" if data.recurring_interval == "month" else "jaarlijks"
            _bilingual_row(
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
            _bilingual_row(pdf, "Purpose / Doel:", f"{en_label} / {nl_label}")

        if data.notes:
            _bilingual_row(pdf, "Notes / Opmerkingen:", data.notes)
        pdf.ln(6)

        # --- ANBI Tax Deductibility Notice (required for Dutch donors) ---
        _render_anbi_notice(pdf)

        # --- Donation ID footer ---
        pdf.divider()
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            4,
            "Auto-generated document / Automatisch gegenereerd document",
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
        pdf.set_text_color(0, 0, 0)

        logger.info(
            "EU tax receipt PDF built for donation_id=%s",
            data.donation_id,
        )
        return pdf


def _bilingual_row(pdf: ShelterPDF, label: str, value: str) -> None:
    """Render a bilingual label: value row."""
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(70, 5, label)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")


def _render_anbi_notice(pdf: ShelterPDF) -> None:
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
