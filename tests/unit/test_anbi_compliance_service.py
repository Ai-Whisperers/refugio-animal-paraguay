"""Unit tests for the ANBI compliance documentation service."""

import re
import zlib
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from src.services.anbi_compliance_service import (
    ANBIComplianceService,
    ANBIDeclarationData,
    ANBILetterData,
    _format_eur,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Decompress all FlateDecode streams in a PDF and return combined text."""
    streams = re.findall(b"stream\r?\n(.+?)\r?\nendstream", pdf_bytes, re.DOTALL)
    parts: list[str] = []
    for stream in streams:
        try:
            parts.append(zlib.decompress(stream).decode("latin-1"))
        except Exception:
            parts.append(stream.decode("latin-1", errors="ignore"))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service() -> ANBIComplianceService:
    """Return a fresh ANBIComplianceService instance."""
    return ANBIComplianceService()


@pytest.fixture
def sample_letter_data() -> ANBILetterData:
    """Return sample ANBI letter data for a Dutch donor."""
    return ANBILetterData(
        donor_id=uuid4(),
        donor_name="Jan de Vries",
        donor_email="jan@example.nl",
        donor_country="NL",
        year=2025,
        total_donated_cents=25000,
        primary_currency="EUR",
        generated_at=datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
    )


@pytest.fixture
def letter_data_no_country() -> ANBILetterData:
    """Return ANBI letter data where donor country is unknown."""
    return ANBILetterData(
        donor_id=uuid4(),
        donor_name="Maria Garcia",
        donor_email="maria@example.es",
        donor_country=None,
        year=2025,
        total_donated_cents=10000,
        primary_currency="EUR",
        generated_at=datetime(2026, 1, 15, tzinfo=UTC),
    )


@pytest.fixture
def letter_data_non_eur() -> ANBILetterData:
    """Return ANBI letter data for a non-EUR donation."""
    return ANBILetterData(
        donor_id=uuid4(),
        donor_name="Carlos Lopez",
        donor_email="carlos@example.py",
        donor_country="PY",
        year=2025,
        total_donated_cents=500000,
        primary_currency="PYG",
        generated_at=datetime(2026, 1, 15, tzinfo=UTC),
    )


@pytest.fixture
def sample_declaration_data() -> ANBIDeclarationData:
    """Return sample ANBI declaration data with fund categories."""
    return ANBIDeclarationData(
        year=2025,
        total_donors=120,
        total_eu_donors=45,
        total_donations_cents=350000,
        total_eur_cents=300000,
        total_pyg_cents=5000000,
        top_fund_categories=[
            ("medical", 150000),
            ("food", 100000),
            ("shelter", 50000),
        ],
        generated_at=datetime(2026, 1, 15, 14, 0, tzinfo=UTC),
        generated_by="admin@refugioanimalparaguay.org",
    )


@pytest.fixture
def declaration_data_no_categories() -> ANBIDeclarationData:
    """Return ANBI declaration data without fund categories."""
    return ANBIDeclarationData(
        year=2024,
        total_donors=80,
        total_eu_donors=30,
        total_donations_cents=200000,
        total_eur_cents=180000,
        total_pyg_cents=2000000,
        top_fund_categories=[],
        generated_at=datetime(2025, 1, 10, 9, 0, tzinfo=UTC),
        generated_by="staff@refugioanimalparaguay.org",
    )


# ---------------------------------------------------------------------------
# _format_eur
# ---------------------------------------------------------------------------


class TestFormatEur:
    def test_zero_cents(self) -> None:
        assert _format_eur(0) == "EUR 0.00"

    def test_whole_euros(self) -> None:
        assert _format_eur(10000) == "EUR 100.00"

    def test_fractional_euros(self) -> None:
        assert _format_eur(2550) == "EUR 25.50"

    def test_large_amount(self) -> None:
        # 3,500.00 EUR
        assert _format_eur(350000) == "EUR 3,500.00"

    def test_one_cent(self) -> None:
        assert _format_eur(1) == "EUR 0.01"


# ---------------------------------------------------------------------------
# generate_donor_letter_bytes
# ---------------------------------------------------------------------------


class TestGenerateDonorLetterBytes:
    def test_returns_bytes(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        assert isinstance(result, bytes)

    def test_returns_valid_pdf(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        assert result[:5] == b"%PDF-"

    def test_pdf_contains_donor_name(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        text = _extract_pdf_text(result)
        assert "Jan de Vries" in text

    def test_pdf_contains_tax_year(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        text = _extract_pdf_text(result)
        assert "2025" in text

    def test_pdf_contains_eur_amount(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        text = _extract_pdf_text(result)
        # EUR 250.00 formatted from 25000 cents
        assert "250.00" in text

    def test_pdf_contains_anbi_reference(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        text = _extract_pdf_text(result)
        assert "ANBI" in text

    def test_pdf_bilingual_content(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        text = _extract_pdf_text(result)
        # Dutch content present
        assert "Belastingdienst" in text or "Wet IB" in text

    def test_generates_without_country(
        self,
        service: ANBIComplianceService,
        letter_data_no_country: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(letter_data_no_country)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_non_eur_currency_shows_raw_amount(
        self,
        service: ANBIComplianceService,
        letter_data_non_eur: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(letter_data_non_eur)
        text = _extract_pdf_text(result)
        assert "PYG" in text

    def test_donor_id_in_footer(
        self,
        service: ANBIComplianceService,
        sample_letter_data: ANBILetterData,
    ) -> None:
        result = service.generate_donor_letter_bytes(sample_letter_data)
        text = _extract_pdf_text(result)
        assert str(sample_letter_data.donor_id) in text


# ---------------------------------------------------------------------------
# generate_declaration_bytes
# ---------------------------------------------------------------------------


class TestGenerateDeclarationBytes:
    def test_returns_bytes(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        assert isinstance(result, bytes)

    def test_returns_valid_pdf(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        assert result[:5] == b"%PDF-"

    def test_pdf_contains_year(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        text = _extract_pdf_text(result)
        assert "2025" in text

    def test_pdf_contains_total_donors(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        text = _extract_pdf_text(result)
        assert "120" in text

    def test_pdf_contains_eu_donors(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        text = _extract_pdf_text(result)
        assert "45" in text

    def test_pdf_contains_fund_categories(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        text = _extract_pdf_text(result)
        assert "medical" in text
        assert "food" in text
        assert "shelter" in text

    def test_pdf_contains_generated_by(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        text = _extract_pdf_text(result)
        assert "admin@refugioanimalparaguay.org" in text

    def test_pdf_without_fund_categories(
        self,
        service: ANBIComplianceService,
        declaration_data_no_categories: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(declaration_data_no_categories)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_internal_document_label(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
    ) -> None:
        result = service.generate_declaration_bytes(sample_declaration_data)
        text = _extract_pdf_text(result)
        assert "INTERNAL" in text

    def test_different_years_produce_different_pdfs(
        self,
        service: ANBIComplianceService,
        sample_declaration_data: ANBIDeclarationData,
        declaration_data_no_categories: ANBIDeclarationData,
    ) -> None:
        result_2025 = service.generate_declaration_bytes(sample_declaration_data)
        result_2024 = service.generate_declaration_bytes(declaration_data_no_categories)
        assert result_2025 != result_2024
