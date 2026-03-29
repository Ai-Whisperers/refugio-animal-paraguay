"""Unit tests for the centralized PDF generation base service."""

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
from fpdf import FPDF
from src.services.pdf_service import (
    BRAND_GRAY,
    BRAND_GREEN,
    BRAND_LIGHT_GRAY,
    SHELTER_ADDRESS,
    SHELTER_EMAIL,
    SHELTER_INFO,
    SHELTER_NAME,
    SHELTER_PHONE,
    SHELTER_WEBSITE,
    BasePDFGenerator,
    PDFGenerationError,
    ShelterPDF,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@dataclass
class _SimpleData:
    message: str


class _SimpleGenerator(BasePDFGenerator):
    """Minimal concrete generator for testing the base class."""

    def _build_pdf(self, data: _SimpleData) -> ShelterPDF:
        pdf = ShelterPDF(title="Test Document")
        pdf.add_page()
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, data.message, new_x="LMARGIN", new_y="NEXT")
        return pdf


class _ErrorGenerator(BasePDFGenerator):
    """Generator that always raises a RuntimeError to test error handling."""

    def _build_pdf(self, data: object) -> FPDF:
        raise RuntimeError("intentional build failure")


# ---------------------------------------------------------------------------
# Shelter constants tests
# ---------------------------------------------------------------------------


class TestShelterConstants:
    def test_shelter_name_is_set(self) -> None:
        assert SHELTER_NAME == "Refugio Animal Paraguay"

    def test_shelter_info_keys(self) -> None:
        assert set(SHELTER_INFO.keys()) == {"name", "address", "phone", "email", "website"}

    def test_shelter_info_values_not_empty(self) -> None:
        for key, value in SHELTER_INFO.items():
            assert value, f"SHELTER_INFO[{key!r}] must not be empty"

    def test_shelter_info_matches_constants(self) -> None:
        assert SHELTER_INFO["name"] == SHELTER_NAME
        assert SHELTER_INFO["address"] == SHELTER_ADDRESS
        assert SHELTER_INFO["phone"] == SHELTER_PHONE
        assert SHELTER_INFO["email"] == SHELTER_EMAIL
        assert SHELTER_INFO["website"] == SHELTER_WEBSITE

    def test_brand_colours_are_valid_rgb(self) -> None:
        for colour in (BRAND_GREEN, BRAND_GRAY, BRAND_LIGHT_GRAY):
            assert len(colour) == 3
            assert all(0 <= c <= 255 for c in colour)


# ---------------------------------------------------------------------------
# ShelterPDF tests
# ---------------------------------------------------------------------------


class TestShelterPDF:
    def test_instantiation_defaults(self) -> None:
        pdf = ShelterPDF()
        assert pdf._doc_title == ""
        assert pdf._show_header is True
        assert pdf._show_footer is True

    def test_instantiation_with_title(self) -> None:
        pdf = ShelterPDF(title="My Document")
        assert pdf._doc_title == "My Document"

    def test_instantiation_header_footer_disabled(self) -> None:
        pdf = ShelterPDF(show_header=False, show_footer=False)
        assert pdf._show_header is False
        assert pdf._show_footer is False

    def test_renders_without_error(self) -> None:
        pdf = ShelterPDF(title="Test")
        pdf.add_page()
        result = pdf.output()
        assert result is not None
        assert len(result) > 0

    def test_output_is_valid_pdf(self) -> None:
        pdf = ShelterPDF(title="Test")
        pdf.add_page()
        raw = pdf.output()
        if isinstance(raw, bytearray):
            raw = bytes(raw)
        assert raw[:5] == b"%PDF-"

    def test_output_with_no_header(self) -> None:
        pdf = ShelterPDF(show_header=False)
        pdf.add_page()
        raw = pdf.output()
        assert raw is not None

    def test_output_with_no_footer(self) -> None:
        pdf = ShelterPDF(show_footer=False)
        pdf.add_page()
        raw = pdf.output()
        assert raw is not None

    def test_auto_page_break_enabled(self) -> None:
        pdf = ShelterPDF()
        assert pdf.auto_page_break is True

    def test_section_title_does_not_raise(self) -> None:
        pdf = ShelterPDF()
        pdf.add_page()
        pdf.section_title("Test Section")  # should not raise

    def test_info_row_does_not_raise(self) -> None:
        pdf = ShelterPDF()
        pdf.add_page()
        pdf.info_row("Label:", "Value")  # should not raise

    def test_info_row_custom_label_width(self) -> None:
        pdf = ShelterPDF()
        pdf.add_page()
        pdf.info_row("Long Label:", "Some value", label_width=80.0)  # should not raise

    def test_divider_does_not_raise(self) -> None:
        pdf = ShelterPDF()
        pdf.add_page()
        pdf.divider()  # should not raise

    def test_multi_page_document(self) -> None:
        pdf = ShelterPDF(title="Multi-page")
        pdf.add_page()
        pdf.set_font("Helvetica", "", 10)
        # Fill enough content to trigger second page
        for _ in range(60):
            pdf.cell(0, 5, "Content line " + "x" * 50, new_x="LMARGIN", new_y="NEXT")
        raw = pdf.output()
        assert raw is not None
        assert pdf.page >= 2


# ---------------------------------------------------------------------------
# BasePDFGenerator tests
# ---------------------------------------------------------------------------


class TestBasePDFGeneratorBytes:
    def test_generate_bytes_returns_bytes(self) -> None:
        generator = _SimpleGenerator()
        result = generator.generate_bytes(_SimpleData(message="Hello"))
        assert isinstance(result, bytes)

    def test_generate_bytes_is_valid_pdf(self) -> None:
        generator = _SimpleGenerator()
        result = generator.generate_bytes(_SimpleData(message="PDF test"))
        assert result[:5] == b"%PDF-"

    def test_generate_bytes_has_content(self) -> None:
        generator = _SimpleGenerator()
        result = generator.generate_bytes(_SimpleData(message="Content"))
        assert len(result) > 1000  # reasonable minimum for a one-page PDF

    def test_generate_bytes_raises_pdf_generation_error_on_failure(self) -> None:
        generator = _ErrorGenerator()
        with pytest.raises(PDFGenerationError, match="intentional build failure"):
            generator.generate_bytes(object())

    def test_generate_bytes_preserves_pdf_generation_error(self) -> None:
        class _DirectErrorGenerator(BasePDFGenerator):
            def _build_pdf(self, data: object) -> FPDF:
                raise PDFGenerationError("direct error")

        generator = _DirectErrorGenerator()
        with pytest.raises(PDFGenerationError, match="direct error"):
            generator.generate_bytes(object())


class TestBasePDFGeneratorFile:
    def test_generate_file_creates_file(self, tmp_path: Path) -> None:
        generator = _SimpleGenerator()
        output = tmp_path / "output.pdf"
        result = generator.generate_file(_SimpleData(message="File test"), output)
        assert result.exists()

    def test_generate_file_returns_path(self, tmp_path: Path) -> None:
        generator = _SimpleGenerator()
        output = tmp_path / "output.pdf"
        result = generator.generate_file(_SimpleData(message="Path test"), output)
        assert isinstance(result, Path)
        assert result == output.resolve()

    def test_generate_file_creates_parent_dirs(self, tmp_path: Path) -> None:
        generator = _SimpleGenerator()
        output = tmp_path / "nested" / "deep" / "output.pdf"
        result = generator.generate_file(_SimpleData(message="Nested"), output)
        assert result.exists()
        assert result.parent.is_dir()

    def test_generate_file_content_is_valid_pdf(self, tmp_path: Path) -> None:
        generator = _SimpleGenerator()
        output = tmp_path / "output.pdf"
        generator.generate_file(_SimpleData(message="Valid PDF"), output)
        with open(output, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_generate_file_raises_on_build_failure(self, tmp_path: Path) -> None:
        generator = _ErrorGenerator()
        output = tmp_path / "output.pdf"
        with pytest.raises(PDFGenerationError):
            generator.generate_file(object(), output)

    def test_generate_file_overwrites_existing(self, tmp_path: Path) -> None:
        generator = _SimpleGenerator()
        output = tmp_path / "output.pdf"
        generator.generate_file(_SimpleData(message="First"), output)
        size1 = output.stat().st_size
        generator.generate_file(_SimpleData(message="Second"), output)
        size2 = output.stat().st_size
        assert output.exists()
        assert abs(size1 - size2) < 500  # similar sizes for similar content

    def test_generate_file_raises_pdf_error_on_io_failure(self, tmp_path: Path) -> None:
        generator = _SimpleGenerator()
        # Use a path where writing will fail (directory instead of file)
        with (
            patch.object(_SimpleGenerator, "_build_pdf", side_effect=OSError("disk full")),
            pytest.raises(PDFGenerationError, match="disk full"),
        ):
            generator.generate_file(_SimpleData(message="Fail"), tmp_path / "out.pdf")


# ---------------------------------------------------------------------------
# PDFGenerationError tests
# ---------------------------------------------------------------------------


class TestPDFGenerationError:
    def test_is_exception(self) -> None:
        err = PDFGenerationError("test message")
        assert isinstance(err, Exception)

    def test_message_preserved(self) -> None:
        err = PDFGenerationError("something went wrong")
        assert str(err) == "something went wrong"

    def test_can_chain_cause(self) -> None:
        cause = ValueError("original cause")
        err = PDFGenerationError("wrapper")
        err.__cause__ = cause
        assert err.__cause__ is cause
