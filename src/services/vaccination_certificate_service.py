"""Vaccination certificate PDF generation service.

Generates bilingual (Spanish/English) vaccination certificates using fpdf2.
Lists all administered vaccinations for an animal with dates, vaccine types,
batch numbers, and administering veterinarian.

Uses the centralized :class:`~src.services.pdf_service.BasePDFGenerator` and
:class:`~src.services.pdf_service.ShelterPDF` for consistent shelter branding.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from uuid import UUID

from src.services.pdf_service import (
    BRAND_GREEN,
    BasePDFGenerator,
    PDFGenerationError,
    ShelterPDF,
)

logger = logging.getLogger(__name__)

# Directory for generated certificates (filesystem storage)
CERTIFICATE_STORAGE_DIR = Path(os.environ.get("CERTIFICATE_STORAGE_DIR", "certificates"))

CERTIFICATE_TITLE = "CERTIFICADO DE VACUNACION / VACCINATION CERTIFICATE"


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VaccinationRecord:
    """Single vaccination entry for the certificate."""

    vaccine_name: str
    administered_date: date
    batch_number: str | None
    administered_by: str | None
    dose_number: int
    next_due_date: date | None


@dataclass(frozen=True)
class CertificateData:
    """Data required to render a vaccination certificate PDF."""

    animal_id: UUID
    animal_name: str
    animal_species: str
    animal_breed: str | None
    animal_birth_date: date | None
    vaccinations: list[VaccinationRecord] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class VaccinationCertificateGenerator(BasePDFGenerator):
    """Generates vaccination certificate PDFs using the centralized ShelterPDF base.

    Produces bilingual (Spanish/English) documents that list all administered
    vaccinations for an animal, including dates, vaccine types, batch numbers,
    and administering veterinarian.

    Example::

        generator = VaccinationCertificateGenerator()
        pdf_bytes = generator.generate_bytes(cert_data)
        pdf_path  = generator.generate_file(cert_data, Path("cert.pdf"))
    """

    def _build_pdf(self, data: CertificateData) -> ShelterPDF:  # type: ignore[override]
        """Build a branded vaccination certificate PDF.

        Args:
            data: :class:`CertificateData` with animal info and vaccination records.

        Returns:
            A fully-populated :class:`~src.services.pdf_service.ShelterPDF` instance.

        Raises:
            :class:`~src.services.pdf_service.PDFGenerationError`: If generation fails.
        """
        if not isinstance(data, CertificateData):
            raise PDFGenerationError("data must be a CertificateData instance")

        pdf = ShelterPDF(title=CERTIFICATE_TITLE)
        pdf.alias_nb_pages()
        pdf.add_page()

        # --- Animal Information section ---
        pdf.section_title("DATOS DEL ANIMAL / ANIMAL INFORMATION")

        breed_text = data.animal_breed or "Mestizo / Mixed"
        birth_text = (
            data.animal_birth_date.isoformat()
            if data.animal_birth_date
            else "Desconocido / Unknown"
        )

        pdf.info_row("Nombre / Name:", data.animal_name)
        pdf.info_row("Especie / Species:", data.animal_species.title())
        pdf.info_row("Raza / Breed:", breed_text)
        pdf.info_row("Nacimiento / Birth:", birth_text)
        pdf.info_row("ID:", str(data.animal_id))
        pdf.ln(4)

        # --- Vaccination record section ---
        pdf.section_title("REGISTRO DE VACUNAS / VACCINATION RECORD")

        if not data.vaccinations:
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(
                0,
                8,
                "No hay vacunas administradas / No vaccines administered",
                new_x="LMARGIN",
                new_y="NEXT",
            )
        else:
            _render_vaccination_table(pdf, data.vaccinations)

        pdf.ln(10)

        # --- Signature area ---
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, "____________________________", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0,
            6,
            "Firma del Veterinario / Veterinarian Signature",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(5)
        pdf.cell(0, 8, "____________________________", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, "Sello del Refugio / Shelter Stamp", new_x="LMARGIN", new_y="NEXT")

        return pdf


def _render_vaccination_table(pdf: ShelterPDF, vaccinations: list[VaccinationRecord]) -> None:
    """Render a formatted vaccination table onto the PDF."""
    col_widths = [45, 25, 15, 30, 35, 40]
    headers = ["Vacuna/Vaccine", "Fecha/Date", "Dosis", "Lote/Batch", "Vet.", "Prox./Next"]

    # Table header row
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(*BRAND_GREEN)
    pdf.set_text_color(255, 255, 255)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 7, header, border=1, fill=True, align="C")
    pdf.ln()

    # Data rows with alternating shading
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 8)
    fill = False
    for vacc in sorted(vaccinations, key=lambda v: v.administered_date):
        fill_color = (240, 240, 240) if fill else (255, 255, 255)
        pdf.set_fill_color(*fill_color)

        pdf.cell(col_widths[0], 6, vacc.vaccine_name[:25], border=1, fill=True)
        pdf.cell(
            col_widths[1], 6, vacc.administered_date.isoformat(), border=1, fill=True, align="C"
        )
        pdf.cell(col_widths[2], 6, str(vacc.dose_number), border=1, fill=True, align="C")
        pdf.cell(col_widths[3], 6, (vacc.batch_number or "-")[:15], border=1, fill=True, align="C")
        pdf.cell(col_widths[4], 6, (vacc.administered_by or "-")[:18], border=1, fill=True)
        next_text = vacc.next_due_date.isoformat() if vacc.next_due_date else "-"
        pdf.cell(col_widths[5], 6, next_text, border=1, fill=True, align="C")
        pdf.ln()
        fill = not fill


# ---------------------------------------------------------------------------
# Backward-compatible function API
# ---------------------------------------------------------------------------

_default_generator = VaccinationCertificateGenerator()


def generate_vaccination_certificate(data: CertificateData) -> Path:
    """Generate a vaccination certificate PDF and return the file path.

    Backward-compatible wrapper around :class:`VaccinationCertificateGenerator`.
    Files are stored under ``CERTIFICATE_STORAGE_DIR``.

    Args:
        data: :class:`CertificateData` with animal info and vaccination records.

    Returns:
        Path to the generated PDF file.

    Raises:
        :class:`~src.services.pdf_service.PDFGenerationError`: If generation fails.
    """
    CERTIFICATE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"vaccination_certificate_{data.animal_id}.pdf"
    output_path = CERTIFICATE_STORAGE_DIR / filename
    return _default_generator.generate_file(data, output_path)
