"""Annual donation summary service.

Generates per-donor annual donation summaries suitable for EU tax submissions.
Covers all completed donations in a given calendar year, with EUR total and
per-donation breakdown.
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
SHELTER_ANBI_RSIN = "RSIN: PENDING REGISTRATION"

PAYMENT_METHOD_LABELS: dict[str, str] = {
    "stripe": "Card (Stripe)",
    "cash": "Cash",
    "transfer": "Bank transfer",
    "sepa_debit": "SEPA Direct Debit",
    "tigo_money": "Tigo Money",
}


@dataclass(frozen=True)
class DonationLineItem:
    """A single donation entry in the annual summary."""

    donation_id: UUID
    date: datetime
    amount_cents: int
    currency: str
    payment_method: str
    fund_category: str | None
    receipt_number: str | None


@dataclass(frozen=True)
class AnnualSummaryData:
    """Data required to render an annual donation summary PDF."""

    donor_id: UUID
    donor_name: str
    donor_email: str
    donor_country: str | None
    year: int
    donations: list[DonationLineItem]
    # Pre-computed totals per currency
    totals_by_currency: dict[str, int]
    generated_at: datetime


def _format_amount(amount_cents: int, currency: str) -> str:
    """Format amount in cents to a human-readable string."""
    if currency == "PYG":
        return f"{amount_cents:,} PYG"
    return f"{amount_cents / 100:,.2f} {currency}"


class AnnualDonationSummaryGenerator:
    """Generates annual donation summary PDFs for EU donor tax submissions."""

    def generate_bytes(self, data: AnnualSummaryData) -> bytes:
        """Generate a PDF summary and return its content as bytes."""
        pdf = self._build_pdf(data)
        content = bytes(pdf.output())
        logger.info(
            "Annual donation summary generated for donor_id=%s year=%d (%d bytes)",
            data.donor_id,
            data.year,
            len(content),
        )
        return content

    def _build_pdf(self, data: AnnualSummaryData) -> FPDF:
        """Build the annual summary PDF document."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        self._render_header(pdf, data)
        self._render_donor_section(pdf, data)
        self._render_summary_totals(pdf, data)
        self._render_donation_table(pdf, data)
        self._render_tax_notice(pdf)
        self._render_footer(pdf, data)

        return pdf

    def _render_header(self, pdf: FPDF, data: AnnualSummaryData) -> None:
        """Render document header."""
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(
            0,
            10,
            f"ANNUAL DONATION SUMMARY {data.year}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            8,
            f"Overzicht Jaardonaties {data.year}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, SHELTER_NAME, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, SHELTER_ADDRESS, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, f"{SHELTER_EMAIL}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, SHELTER_ANBI_RSIN, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)

        pdf.set_draw_color(60, 120, 180)
        pdf.set_line_width(0.5)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(6)

    def _render_donor_section(self, pdf: FPDF, data: AnnualSummaryData) -> None:
        """Render donor identification."""
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Donor / Donateur", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

        self._row(pdf, "Name / Naam:", data.donor_name)
        self._row(pdf, "Email:", data.donor_email)
        if data.donor_country:
            self._row(pdf, "Country / Land:", data.donor_country)
        self._row(
            pdf,
            "Issued / Datum uitgifte:",
            data.generated_at.strftime("%d/%m/%Y"),
        )
        pdf.ln(6)

    def _render_summary_totals(self, pdf: FPDF, data: AnnualSummaryData) -> None:
        """Render total amounts per currency."""
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"Year Total {data.year} / Jaartotaal", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

        pdf.set_font("Helvetica", "", 9)
        self._row(pdf, "Donations / Donaties:", str(len(data.donations)))

        if data.totals_by_currency:
            for currency, total_cents in sorted(data.totals_by_currency.items()):
                self._row(
                    pdf,
                    f"Total {currency} / Totaal {currency}:",
                    _format_amount(total_cents, currency),
                )
        else:
            self._row(pdf, "Total / Totaal:", "No completed donations")

        pdf.ln(8)

    def _render_donation_table(self, pdf: FPDF, data: AnnualSummaryData) -> None:
        """Render table of individual donations."""
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Donations / Overzicht Donaties", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

        if not data.donations:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(
                0,
                6,
                "No completed donations recorded for this period.",
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.set_text_color(0, 0, 0)
            pdf.ln(6)
            return

        # Table header
        col_widths = [28, 22, 22, 40, 40, 28]
        headers = ["Date", "Amount", "Currency", "Method", "Fund", "Receipt"]

        pdf.set_fill_color(220, 235, 250)
        pdf.set_font("Helvetica", "B", 8)
        for header, width in zip(headers, col_widths, strict=True):
            pdf.cell(width, 6, header, border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for idx, item in enumerate(data.donations):
            fill = idx % 2 == 0
            if fill:
                pdf.set_fill_color(248, 252, 255)
            else:
                pdf.set_fill_color(255, 255, 255)

            row = [
                item.date.strftime("%d/%m/%Y"),
                _format_amount(item.amount_cents, item.currency),
                item.currency,
                PAYMENT_METHOD_LABELS.get(item.payment_method, item.payment_method)[:18],
                (item.fund_category or "general")[:18],
                (item.receipt_number or str(item.donation_id)[:8])[:12],
            ]
            for value, width in zip(row, col_widths, strict=True):
                pdf.cell(width, 5, value, border=1, fill=fill)
            pdf.ln()

        pdf.ln(8)

    def _render_tax_notice(self, pdf: FPDF) -> None:
        """Render EU/Dutch tax deductibility guidance."""
        pdf.set_fill_color(240, 247, 255)
        pdf.set_draw_color(60, 120, 180)
        box_y = pdf.get_y()
        pdf.rect(pdf.l_margin, box_y, pdf.w - pdf.l_margin - pdf.r_margin, 24, style="FD")
        pdf.set_y(box_y + 3)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(30, 80, 150)
        pdf.cell(0, 5, "For Tax Purposes / Belastingdienst", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(
            0,
            4,
            "This document serves as an annual overview of charitable gifts to Refugio Animal "
            "Paraguay. For Dutch tax deductions (giftenaftrek), retain this document with your "
            "tax records. Consult belastingdienst.nl or your tax advisor.",
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

    def _render_footer(self, pdf: FPDF, data: AnnualSummaryData) -> None:
        """Render document footer."""
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            4,
            f"Annual summary generated by {SHELTER_NAME} on {data.generated_at.strftime('%d/%m/%Y')}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            4,
            f"Donor ID: {data.donor_id} | Tax Year: {data.year}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    @staticmethod
    def _row(pdf: FPDF, label: str, value: str) -> None:
        """Render a label-value row."""
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(65, 5, label)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")
