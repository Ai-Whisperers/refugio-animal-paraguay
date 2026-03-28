"""ANBI compliance documentation service.

Generates ANBI (Algemeen Nut Beogende Instelling) compliance documents for
the shelter's Dutch donors. ANBI is the Dutch tax authority designation for
public benefit organizations, enabling donors to deduct gifts.

This service produces:
1. Annual ANBI declaration summary (for shelther internal compliance)
2. Donor-facing ANBI information letter
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
SHELTER_WEBSITE = "https://refugioanimalparaguay.org"

# Placeholder values - to be updated when ANBI registration is obtained
SHELTER_ANBI_RSIN = "RSIN: PENDING"
SHELTER_BANK_IBAN = "IBAN: NL00 XXXX 0000 0000 00"
CURRENT_TAX_YEAR = datetime.now().year


@dataclass(frozen=True)
class ANBILetterData:
    """Data for generating an ANBI information letter for a specific donor."""

    donor_id: UUID
    donor_name: str
    donor_email: str
    donor_country: str | None
    year: int
    total_donated_cents: int
    primary_currency: str
    generated_at: datetime


@dataclass(frozen=True)
class ANBIDeclarationData:
    """Data for the annual ANBI compliance declaration (internal document)."""

    year: int
    total_donors: int
    total_eu_donors: int
    total_donations_cents: int
    total_eur_cents: int
    total_pyg_cents: int
    top_fund_categories: list[tuple[str, int]]
    generated_at: datetime
    generated_by: str


def _format_eur(amount_cents: int) -> str:
    """Format EUR cents to readable string."""
    return f"EUR {amount_cents / 100:,.2f}"


class ANBIComplianceService:
    """Generates ANBI compliance documents for Dutch regulatory purposes."""

    def generate_donor_letter_bytes(self, data: ANBILetterData) -> bytes:
        """Generate an ANBI information letter for a specific donor.

        This letter confirms the shelter's charitable status and informs
        the donor about the conditions for Dutch tax deductibility.
        """
        pdf = self._build_donor_letter(data)
        content = bytes(pdf.output())
        logger.info(
            "ANBI donor letter generated for donor_id=%s year=%d (%d bytes)",
            data.donor_id,
            data.year,
            len(content),
        )
        return content

    def generate_declaration_bytes(self, data: ANBIDeclarationData) -> bytes:
        """Generate the annual ANBI compliance declaration (internal document)."""
        pdf = self._build_declaration(data)
        content = bytes(pdf.output())
        logger.info(
            "ANBI declaration generated for year=%d (%d bytes)",
            data.year,
            len(content),
        )
        return content

    def _build_donor_letter(self, data: ANBILetterData) -> FPDF:
        """Build the ANBI donor information letter PDF."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(
            0,
            10,
            "ANBI Gift Confirmation / ANBI Giftenbevestiging",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, SHELTER_NAME, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0, 5, f"{SHELTER_EMAIL} | {SHELTER_WEBSITE}", align="C", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

        pdf.set_draw_color(60, 120, 180)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(6)

        # Addressee
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Addressed to / Gericht aan", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(55, 5, "Name / Naam:")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, data.donor_name, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(55, 5, "Email:")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, data.donor_email, new_x="LMARGIN", new_y="NEXT")

        if data.donor_country:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(55, 5, "Country / Land:")
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, data.donor_country, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(55, 5, "Tax Year / Belastingjaar:")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, str(data.year), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # Donation confirmation
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Donation Confirmation / Donatiebewijs", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

        pdf.set_font("Helvetica", "", 9)
        amount_str = (
            _format_eur(data.total_donated_cents)
            if data.primary_currency == "EUR"
            else f"{data.total_donated_cents} {data.primary_currency}"
        )
        pdf.multi_cell(
            0,
            5,
            f"This letter confirms that {data.donor_name} made charitable donations totalling "
            f"{amount_str} to {SHELTER_NAME} during the tax year {data.year}.",
        )
        pdf.ln(3)
        pdf.multi_cell(
            0,
            5,
            f"Dit schrijven bevestigt dat {data.donor_name} gedurende het belastingjaar {data.year} "
            f"giften heeft gedaan aan {SHELTER_NAME} voor een totaalbedrag van {amount_str}.",
        )
        pdf.ln(6)

        # ANBI information box
        pdf.set_fill_color(240, 247, 255)
        pdf.set_draw_color(60, 120, 180)
        box_y = pdf.get_y()
        pdf.rect(pdf.l_margin, box_y, pdf.w - pdf.l_margin - pdf.r_margin, 50, style="FD")
        pdf.set_y(box_y + 3)

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 80, 150)
        pdf.cell(0, 5, "ANBI & Tax Deduction / Belastingaftrek", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(
            0,
            4,
            "EN: Refugio Animal Paraguay is a foreign charitable organization. Dutch tax residents "
            "may be eligible to deduct donations to qualifying foreign charities under Article 6.33 "
            "of the Dutch Income Tax Act (Wet IB 2001). Please consult the Belastingdienst or "
            "your tax advisor to verify deductibility for your specific situation.",
        )
        pdf.ln(2)
        pdf.multi_cell(
            0,
            4,
            "NL: Refugio Animal Paraguay is een buitenlandse instelling voor het algemeen nut. "
            "Nederlandse belastingplichtigen kunnen mogelijk giften aan erkende buitenlandse "
            "instellingen aftrekken op grond van artikel 6.33 Wet IB 2001. Raadpleeg de "
            "Belastingdienst of uw belastingadviseur voor uw persoonlijke situatie.",
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

        # Footer
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            4,
            f"Generated by {SHELTER_NAME} on {data.generated_at.strftime('%d/%m/%Y')} | {SHELTER_ANBI_RSIN}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.cell(
            0,
            4,
            f"Donor ID: {data.donor_id}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        return pdf

    def _build_declaration(self, data: ANBIDeclarationData) -> FPDF:
        """Build the annual ANBI compliance declaration PDF (internal)."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(
            0,
            10,
            f"ANBI Annual Compliance Declaration {data.year}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0, 5, f"{SHELTER_NAME} - INTERNAL DOCUMENT", align="C", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_text_color(0, 0, 0)
        pdf.ln(6)

        pdf.set_draw_color(60, 120, 180)
        pdf.set_line_width(0.4)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(6)

        # Stats
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, f"Donation Statistics {data.year}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

        rows = [
            ("Total donors:", str(data.total_donors)),
            ("EU donors:", str(data.total_eu_donors)),
            ("Total donations:", _format_eur(data.total_donations_cents)),
            ("EUR donations:", _format_eur(data.total_eur_cents)),
            ("PYG donations:", f"{data.total_pyg_cents:,} PYG"),
        ]
        for label, value in rows:
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(65, 5, label)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, value, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

        if data.top_fund_categories:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 7, "Fund Allocation", new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(180, 180, 180)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)

            for category, total_cents in data.top_fund_categories:
                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(65, 5, f"{category}:")
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 5, _format_eur(total_cents), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)

        # Generated by
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            0,
            5,
            f"Generated by: {data.generated_by} on {data.generated_at.strftime('%d/%m/%Y %H:%M')}",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_text_color(0, 0, 0)

        return pdf
