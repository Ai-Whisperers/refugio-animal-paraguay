"""ANBI compliance documentation service.

Generates ANBI (Algemeen Nut Beogende Instelling) compliance documents for
the shelter's Dutch donors. ANBI is the Dutch tax authority designation for
public benefit organizations, enabling donors to deduct gifts.

This service produces:
1. Annual ANBI declaration summary (for shelter internal compliance)
2. Donor-facing ANBI information letter

Uses the centralized :class:`~src.services.pdf_service.BasePDFGenerator` and
:class:`~src.services.pdf_service.ShelterPDF` for consistent shelter branding.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.services.pdf_service import BasePDFGenerator, ShelterPDF

logger = logging.getLogger(__name__)

# Placeholder values - to be updated when ANBI registration is obtained
SHELTER_ANBI_RSIN = "RSIN: PENDING"
SHELTER_BANK_IBAN = "IBAN: NL00 XXXX 0000 0000 00"
CURRENT_TAX_YEAR = datetime.now().year

DONOR_LETTER_TITLE = "ANBI GIFT CONFIRMATION / ANBI GIFTENBEVESTIGING"
DECLARATION_TITLE = "ANBI ANNUAL COMPLIANCE DECLARATION"


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


class ANBIDonorLetterGenerator(BasePDFGenerator):
    """Generates ANBI donor information letters using ShelterPDF branding.

    Example::

        generator = ANBIDonorLetterGenerator()
        pdf_bytes = generator.generate_bytes(letter_data)
    """

    def _build_pdf(self, data: ANBILetterData) -> ShelterPDF:  # type: ignore[override]
        """Build the ANBI donor information letter PDF."""
        pdf = ShelterPDF(title=DONOR_LETTER_TITLE)
        pdf.add_page()

        # Addressee section
        pdf.section_title("Addressed to / Gericht aan")
        pdf.info_row("Name / Naam:", data.donor_name)
        pdf.info_row("Email:", data.donor_email)
        if data.donor_country:
            pdf.info_row("Country / Land:", data.donor_country)
        pdf.info_row("Tax Year / Belastingjaar:", str(data.year))
        pdf.ln(4)

        # Donation confirmation
        pdf.section_title("Donation Confirmation / Donatiebewijs")
        amount_str = (
            _format_eur(data.total_donated_cents)
            if data.primary_currency == "EUR"
            else f"{data.total_donated_cents} {data.primary_currency}"
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(
            0,
            5,
            f"This letter confirms that {data.donor_name} made charitable donations totalling "
            f"{amount_str} to Refugio Animal Paraguay during the tax year {data.year}.",
        )
        pdf.ln(3)
        pdf.multi_cell(
            0,
            5,
            f"Dit schrijven bevestigt dat {data.donor_name} gedurende het belastingjaar {data.year} "
            f"giften heeft gedaan aan Refugio Animal Paraguay voor een totaalbedrag van {amount_str}.",
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

        # Donor ID line above auto footer
        pdf.set_y(-30)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            4,
            f"Donor ID: {data.donor_id} | {SHELTER_ANBI_RSIN}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_text_color(0, 0, 0)

        return pdf


class ANBIDeclarationGenerator(BasePDFGenerator):
    """Generates annual ANBI compliance declarations using ShelterPDF branding.

    Example::

        generator = ANBIDeclarationGenerator()
        pdf_bytes = generator.generate_bytes(declaration_data)
    """

    def _build_pdf(self, data: ANBIDeclarationData) -> ShelterPDF:  # type: ignore[override]
        """Build the annual ANBI compliance declaration PDF (internal)."""
        pdf = ShelterPDF(title=f"{DECLARATION_TITLE} {data.year}")
        pdf.add_page()

        # Internal document label
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "INTERNAL DOCUMENT", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        # Donation statistics
        pdf.section_title(f"Donation Statistics {data.year}")
        rows = [
            ("Total donors:", str(data.total_donors)),
            ("EU donors:", str(data.total_eu_donors)),
            ("Total donations:", _format_eur(data.total_donations_cents)),
            ("EUR donations:", _format_eur(data.total_eur_cents)),
            ("PYG donations:", f"{data.total_pyg_cents:,} PYG"),
        ]
        for label, value in rows:
            pdf.info_row(label, value, label_width=65)
        pdf.ln(4)

        if data.top_fund_categories:
            pdf.section_title("Fund Allocation")
            for category, total_cents in data.top_fund_categories:
                pdf.info_row(f"{category}:", _format_eur(total_cents), label_width=65)
            pdf.ln(4)

        # Generated-by attribution
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


class ANBIComplianceService:
    """Facade for generating ANBI compliance documents for Dutch regulatory purposes.

    Delegates to :class:`ANBIDonorLetterGenerator` and
    :class:`ANBIDeclarationGenerator` for consistent shelter branding.
    """

    def __init__(self) -> None:
        self._letter_generator = ANBIDonorLetterGenerator()
        self._declaration_generator = ANBIDeclarationGenerator()

    def generate_donor_letter_bytes(self, data: ANBILetterData) -> bytes:
        """Generate an ANBI information letter for a specific donor.

        This letter confirms the shelter's charitable status and informs
        the donor about the conditions for Dutch tax deductibility.
        """
        content = self._letter_generator.generate_bytes(data)
        logger.info(
            "ANBI donor letter generated for donor_id=%s year=%d (%d bytes)",
            data.donor_id,
            data.year,
            len(content),
        )
        return content

    def generate_declaration_bytes(self, data: ANBIDeclarationData) -> bytes:
        """Generate the annual ANBI compliance declaration (internal document)."""
        content = self._declaration_generator.generate_bytes(data)
        logger.info(
            "ANBI declaration generated for year=%d (%d bytes)",
            data.year,
            len(content),
        )
        return content
