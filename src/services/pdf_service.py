"""Centralized PDF generation service for Refugio Animal Paraguay.

Provides a shared foundation for all PDF documents:
- Common shelter branding constants
- ``ShelterPDF`` — FPDF subclass with automatic header and footer
- ``BasePDFGenerator`` — abstract base class for all document generators
- ``PDFGenerationError`` — raised on generation failures

Usage::

    from src.services.pdf_service import BasePDFGenerator, ShelterPDF

    class MyDocumentGenerator(BasePDFGenerator):
        def _build_pdf(self, data: MyData) -> ShelterPDF:
            pdf = ShelterPDF(title="My Document")
            pdf.add_page()
            # ... populate document ...
            return pdf
"""

import io
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shelter identity constants — single source of truth for all PDF documents
# ---------------------------------------------------------------------------

SHELTER_NAME = "Refugio Animal Paraguay"
SHELTER_ADDRESS = "Asuncion, Paraguay"
SHELTER_PHONE = "+595 21 000 0000"
SHELTER_EMAIL = "info@refugioanimalparaguay.org"
SHELTER_WEBSITE = "www.refugioanimalparaguay.org"

SHELTER_INFO: dict[str, str] = {
    "name": SHELTER_NAME,
    "address": SHELTER_ADDRESS,
    "phone": SHELTER_PHONE,
    "email": SHELTER_EMAIL,
    "website": SHELTER_WEBSITE,
}

# Brand colours (RGB)
BRAND_GREEN = (0, 102, 51)
BRAND_GRAY = (100, 100, 100)
BRAND_LIGHT_GRAY = (200, 200, 200)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""


# ---------------------------------------------------------------------------
# ShelterPDF — FPDF subclass with shelter header and footer
# ---------------------------------------------------------------------------


class ShelterPDF(FPDF):
    """FPDF subclass that renders a shelter-branded header and footer on every page.

    Args:
        title: Document title shown in the header below the shelter name.
        show_header: Whether to render the shelter header (default ``True``).
        show_footer: Whether to render the page-number footer (default ``True``).
    """

    def __init__(
        self,
        title: str = "",
        show_header: bool = True,
        show_footer: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._doc_title = title
        self._show_header = show_header
        self._show_footer = show_footer
        self.set_auto_page_break(auto=True, margin=25)

    # ------------------------------------------------------------------
    # fpdf2 overrides
    # ------------------------------------------------------------------

    def header(self) -> None:
        if not self._show_header:
            return

        # Shelter name
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*BRAND_GREEN)
        self.cell(0, 10, SHELTER_NAME, new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_text_color(0, 0, 0)

        # Contact line
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*BRAND_GRAY)
        contact_line = f"{SHELTER_ADDRESS}  |  {SHELTER_PHONE}  |  {SHELTER_EMAIL}"
        self.cell(0, 5, contact_line, new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_text_color(0, 0, 0)

        # Divider
        self.set_draw_color(*BRAND_GREEN)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y() + 1, self.w - self.r_margin, self.get_y() + 1)
        self.ln(4)

        # Document title
        if self._doc_title:
            self.set_font("Helvetica", "B", 13)
            self.cell(0, 8, self._doc_title.upper(), new_x="LMARGIN", new_y="NEXT", align="C")
            self.ln(3)

    def footer(self) -> None:
        if not self._show_footer:
            return

        self.set_y(-20)
        self.set_draw_color(*BRAND_LIGHT_GRAY)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*BRAND_GRAY)

        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        self.cell(0, 5, f"Generado: {timestamp}", align="L", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, f"Pagina {self.page_no()}/{{nb}}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    # ------------------------------------------------------------------
    # Helper drawing methods available to all document subclasses
    # ------------------------------------------------------------------

    def section_title(self, title: str) -> None:
        """Render a bold section heading followed by a thin grey rule."""
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*BRAND_LIGHT_GRAY)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)
        self.set_font("Helvetica", "", 10)

    def info_row(self, label: str, value: str, label_width: float = 55.0) -> None:
        """Render a ``label: value`` line in 10pt body font."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*BRAND_GRAY)
        self.cell(label_width, 6, label)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    def divider(self) -> None:
        """Render a full-width horizontal rule."""
        self.set_draw_color(*BRAND_LIGHT_GRAY)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)


# ---------------------------------------------------------------------------
# BasePDFGenerator — abstract base for concrete document generators
# ---------------------------------------------------------------------------


class BasePDFGenerator(ABC):
    """Abstract base class for all Refugio PDF document generators.

    Concrete subclasses implement ``_build_pdf`` which returns a populated
    ``ShelterPDF`` (or any ``FPDF``) instance. The base class provides
    ``generate_bytes`` and ``generate_file`` so callers have a consistent API.

    Example::

        class ContractGenerator(BasePDFGenerator):
            def _build_pdf(self, data: ContractData) -> ShelterPDF:
                pdf = ShelterPDF(title="Contrato de Adopcion")
                pdf.add_page()
                pdf.info_row("Adoptante:", data.adopter_name)
                return pdf

        generator = ContractGenerator()
        pdf_bytes = generator.generate_bytes(my_data)
        pdf_path  = generator.generate_file(my_data, output_path)
    """

    @abstractmethod
    def _build_pdf(self, data: Any) -> FPDF:
        """Build and return a populated FPDF instance.

        Args:
            data: Document-specific data object.

        Returns:
            A fully-populated ``FPDF`` instance ready for output.
        """

    def generate_bytes(self, data: Any) -> bytes:
        """Generate the PDF and return its content as ``bytes``.

        Args:
            data: Document-specific data object passed to ``_build_pdf``.

        Returns:
            Raw PDF bytes suitable for HTTP streaming.

        Raises:
            PDFGenerationError: If generation fails for any reason.
        """
        try:
            pdf = self._build_pdf(data)
            raw = pdf.output()
            if isinstance(raw, bytearray):
                return bytes(raw)
            if isinstance(raw, bytes):
                return raw
            # Fallback: use StringIO-compatible output
            buf = io.BytesIO()
            pdf.output(buf)  # type: ignore[arg-type]
            return buf.getvalue()
        except PDFGenerationError:
            raise
        except Exception as exc:
            raise PDFGenerationError(f"PDF generation failed: {exc}") from exc

    def generate_file(self, data: Any, output_path: Path) -> Path:
        """Generate the PDF and write it to ``output_path``.

        Parent directories are created automatically.

        Args:
            data: Document-specific data object passed to ``_build_pdf``.
            output_path: Destination file path (must end in ``.pdf``).

        Returns:
            The resolved ``output_path``.

        Raises:
            PDFGenerationError: If generation or writing fails.
        """
        try:
            output_path = output_path.resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            pdf = self._build_pdf(data)
            pdf.output(str(output_path))
            logger.info("PDF written to %s", output_path)
            return output_path
        except PDFGenerationError:
            raise
        except Exception as exc:
            raise PDFGenerationError(
                f"PDF generation failed writing to {output_path}: {exc}"
            ) from exc
