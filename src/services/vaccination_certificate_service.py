"""Vaccination certificate PDF generation service.

Generates bilingual (Spanish/English) vaccination certificates using fpdf2.
Lists all administered vaccinations for an animal with dates, vaccine types,
batch numbers, and administering veterinarian.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import UUID

from fpdf import FPDF

logger = logging.getLogger(__name__)

# Directory for generated certificates
CERTIFICATE_STORAGE_DIR = Path(os.environ.get("CERTIFICATE_STORAGE_DIR", "certificates"))

SHELTER_NAME = "Refugio Animal Paraguay"
SHELTER_ADDRESS = "Asuncion, Paraguay"
SHELTER_PHONE = "+595 21 000 0000"
SHELTER_EMAIL = "info@refugioanimalparaguay.org"


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


class VaccinationCertificatePDF(FPDF):
    """Custom FPDF subclass for vaccination certificates."""

    def header(self) -> None:
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, SHELTER_NAME, new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("Helvetica", "", 9)
        self.cell(
            0,
            5,
            f"{SHELTER_ADDRESS} | {SHELTER_PHONE} | {SHELTER_EMAIL}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self.ln(3)
        self.set_font("Helvetica", "B", 14)
        self.cell(
            0,
            10,
            "CERTIFICADO DE VACUNACION / VACCINATION CERTIFICATE",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self.ln(5)
        # Divider line
        self.set_draw_color(0, 102, 51)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self) -> None:
        self.set_y(-25)
        self.set_font("Helvetica", "I", 8)
        self.cell(
            0,
            5,
            f"Generado el / Generated on: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
        self.cell(
            0,
            5,
            f"Pagina / Page {self.page_no()}/{{nb}}",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )


def generate_vaccination_certificate(data: CertificateData) -> Path:
    """Generate a vaccination certificate PDF and return the file path.

    Args:
        data: Certificate data including animal info and vaccination records.

    Returns:
        Path to the generated PDF file.
    """
    CERTIFICATE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    pdf = VaccinationCertificatePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=30)

    # Animal Information
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "DATOS DEL ANIMAL / ANIMAL INFORMATION", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)

    breed_text = data.animal_breed or "Mestizo / Mixed"
    birth_text = (
        data.animal_birth_date.isoformat() if data.animal_birth_date else "Desconocido / Unknown"
    )

    info_lines = [
        f"Nombre / Name: {data.animal_name}",
        f"Especie / Species: {data.animal_species.title()}",
        f"Raza / Breed: {breed_text}",
        f"Fecha de nacimiento / Birth date: {birth_text}",
        f"ID: {data.animal_id}",
    ]
    for line in info_lines:
        pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # Vaccination Table
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "REGISTRO DE VACUNAS / VACCINATION RECORD", new_x="LMARGIN", new_y="NEXT")

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
        # Table header
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(0, 102, 51)
        pdf.set_text_color(255, 255, 255)

        col_widths = [45, 25, 15, 30, 35, 40]
        headers = ["Vacuna/Vaccine", "Fecha/Date", "Dosis", "Lote/Batch", "Vet.", "Prox./Next"]

        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 7, header, border=1, fill=True, align="C")
        pdf.ln()

        # Table rows
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 8)
        fill = False
        for vacc in sorted(data.vaccinations, key=lambda v: v.administered_date):
            if fill:
                pdf.set_fill_color(240, 240, 240)
            else:
                pdf.set_fill_color(255, 255, 255)

            pdf.cell(col_widths[0], 6, vacc.vaccine_name[:25], border=1, fill=True)
            pdf.cell(
                col_widths[1], 6, vacc.administered_date.isoformat(), border=1, fill=True, align="C"
            )
            pdf.cell(col_widths[2], 6, str(vacc.dose_number), border=1, fill=True, align="C")
            pdf.cell(
                col_widths[3], 6, (vacc.batch_number or "-")[:15], border=1, fill=True, align="C"
            )
            pdf.cell(col_widths[4], 6, (vacc.administered_by or "-")[:18], border=1, fill=True)
            next_text = vacc.next_due_date.isoformat() if vacc.next_due_date else "-"
            pdf.cell(col_widths[5], 6, next_text, border=1, fill=True, align="C")
            pdf.ln()
            fill = not fill

    pdf.ln(15)

    # Signature area
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, "____________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Firma del Veterinario / Veterinarian Signature", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.cell(0, 8, "____________________________", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Sello del Refugio / Shelter Stamp", new_x="LMARGIN", new_y="NEXT")

    # Save
    filename = f"vaccination_certificate_{data.animal_id}.pdf"
    filepath = CERTIFICATE_STORAGE_DIR / filename
    pdf.output(str(filepath))
    logger.info("Generated vaccination certificate: %s", filepath)
    return filepath
