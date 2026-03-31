"""Adoption contract PDF generation service.

Generates Spanish-language adoption contracts using fpdf2 and stores
them on the local filesystem. The generated PDF path is recorded on
the adoption_request row for later retrieval.

Uses the centralized :class:`~src.services.pdf_service.BasePDFGenerator` and
:class:`~src.services.pdf_service.ShelterPDF` for consistent shelter branding.
"""

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from src.services.pdf_service import BasePDFGenerator, ShelterPDF

logger = logging.getLogger(__name__)

# Directory where generated contracts are stored.
# Configurable via CONTRACT_STORAGE_DIR env var; defaults to ./contracts/
CONTRACT_STORAGE_DIR = Path(os.environ.get("CONTRACT_STORAGE_DIR", "contracts"))

# Adoption commitment clauses in Spanish (Paraguayan context)
COMMITMENT_CLAUSES = [
    (
        "1. El adoptante se compromete a brindar al animal adoptado "
        "atención veterinaria adecuada, incluyendo vacunaciones anuales, "
        "desparasitación y atención en caso de enfermedad o lesión."
    ),
    (
        "2. El adoptante se compromete a no ceder, vender ni abandonar "
        "al animal bajo ninguna circunstancia. En caso de no poder "
        "continuar con el cuidado del animal, deberá contactar al "
        "Refugio Animal Paraguay para coordinar su retorno."
    ),
    (
        "3. El adoptante autoriza al Refugio Animal Paraguay a realizar "
        "visitas de seguimiento domiciliario durante los primeros 12 "
        "meses post-adopción."
    ),
    (
        "4. El adoptante se compromete a mantener al animal en condiciones "
        "de bienestar, con alimentación adecuada, espacio suficiente y "
        "trato digno."
    ),
]


@dataclass(frozen=True)
class ContractData:
    """Data required to render an adoption contract PDF."""

    request_id: UUID
    adopter_name: str
    adopter_email: str
    adopter_phone: str | None
    adopter_address: str | None
    animal_name: str
    animal_species: str
    animal_breed: str | None
    approved_at: datetime | None


class ContractPDFGenerator(BasePDFGenerator):
    """Generates adoption contract PDFs using the centralized ShelterPDF base.

    Example::

        generator = ContractPDFGenerator()
        pdf_bytes = generator.generate_bytes(contract_data)
        pdf_path  = generator.generate(contract_data)
    """

    def __init__(self, storage_dir: Path | None = None) -> None:
        self._storage_dir = storage_dir or CONTRACT_STORAGE_DIR

    def generate(self, data: ContractData) -> Path:
        """Generate a PDF contract and return its file path.

        Creates the storage directory if it doesn't exist. File is stored
        at ``<storage_dir>/<request_id>/contract.pdf``.
        """
        output_dir = self._storage_dir / str(data.request_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "contract.pdf"

        pdf = self._build_pdf(data)
        pdf.output(str(output_path))

        logger.info(
            "Contract PDF generated for request_id=%s at %s",
            data.request_id,
            output_path,
        )
        return output_path

    def _build_pdf(self, data: ContractData) -> ShelterPDF:  # type: ignore[override]
        """Build the PDF document in memory."""
        pdf = ShelterPDF(title="CONTRATO DE ADOPCION RESPONSABLE")
        pdf.add_page()

        pdf.ln(4)

        # --- Adopter Section ---
        self._section_title(pdf, "Datos del Adoptante")
        self._info_row(pdf, "Nombre completo:", data.adopter_name)
        self._info_row(pdf, "Email:", data.adopter_email)
        if data.adopter_phone:
            self._info_row(pdf, "Telefono:", data.adopter_phone)
        if data.adopter_address:
            self._info_row(pdf, "Direccion:", data.adopter_address)
        pdf.ln(4)

        # --- Animal Section ---
        self._section_title(pdf, "Datos del Animal")
        self._info_row(pdf, "Nombre:", data.animal_name)
        self._info_row(pdf, "Especie:", data.animal_species)
        if data.animal_breed:
            self._info_row(pdf, "Raza:", data.animal_breed)
        pdf.ln(4)

        # --- Commitment Clauses ---
        self._section_title(pdf, "Compromisos del Adoptante")
        pdf.set_font("Helvetica", "", 10)
        for clause in COMMITMENT_CLAUSES:
            pdf.multi_cell(0, 5, clause)
            pdf.ln(3)
        pdf.ln(4)

        # --- Signature Section ---
        y_pos = pdf.get_y()
        if y_pos > 230:
            pdf.add_page()

        pdf.ln(16)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_draw_color(30, 30, 30)

        # Adopter signature
        x_start = pdf.l_margin
        line_width = 70.0
        pdf.line(x_start, pdf.get_y(), x_start + line_width, pdf.get_y())
        pdf.ln(2)
        pdf.cell(line_width, 5, "Firma del Adoptante")
        pdf.ln(4)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(line_width, 5, data.adopter_name)
        pdf.set_text_color(0, 0, 0)

        # Shelter signature (right side)
        pdf.set_xy(x_start + 110, y_pos + 16)
        pdf.line(x_start + 110, pdf.get_y(), x_start + 110 + line_width, pdf.get_y())
        pdf.ln(2)
        pdf.cell(line_width, 5, "Por el Refugio Animal Paraguay")
        pdf.ln(4)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(line_width, 5, "Representante Legal")
        pdf.set_text_color(0, 0, 0)

        # --- Footer ---
        generated_str = (
            data.approved_at.strftime("%d/%m/%Y")
            if data.approved_at
            else datetime.now(UTC).strftime("%d/%m/%Y")
        )
        pdf.set_y(-20)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0,
            5,
            f"Contrato N: {data.request_id} | Generado: {generated_str}",
            align="C",
        )

        return pdf

    @staticmethod
    def _section_title(pdf: ShelterPDF, title: str) -> None:
        """Render a section title with underline."""
        pdf.section_title(title)

    @staticmethod
    def _info_row(pdf: ShelterPDF, label: str, value: str) -> None:
        """Render a label: value row."""
        pdf.info_row(label, value)
