"""Unit tests for the adoption contract PDF generation service."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from src.services.contract_service import (
    COMMITMENT_CLAUSES,
    ContractData,
    ContractPDFGenerator,
)


@pytest.fixture
def sample_contract_data() -> ContractData:
    """A complete ContractData instance for testing."""
    return ContractData(
        request_id=uuid4(),
        adopter_name="Maria Garcia",
        adopter_email="maria@example.com",
        adopter_phone="+595981234567",
        adopter_address="Asuncion, Paraguay",
        animal_name="Luna",
        animal_species="dog",
        animal_breed="Labrador Mix",
        approved_at=datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def minimal_contract_data() -> ContractData:
    """A ContractData with optional fields set to None."""
    return ContractData(
        request_id=uuid4(),
        adopter_name="Carlos Lopez",
        adopter_email="carlos@example.com",
        adopter_phone=None,
        adopter_address=None,
        animal_name="Max",
        animal_species="cat",
        animal_breed=None,
        approved_at=None,
    )


class TestContractData:
    """Tests for the ContractData dataclass."""

    def test_all_fields_set(self, sample_contract_data: ContractData) -> None:
        assert sample_contract_data.adopter_name == "Maria Garcia"
        assert sample_contract_data.animal_name == "Luna"
        assert sample_contract_data.animal_breed == "Labrador Mix"

    def test_optional_fields_none(self, minimal_contract_data: ContractData) -> None:
        assert minimal_contract_data.adopter_phone is None
        assert minimal_contract_data.adopter_address is None
        assert minimal_contract_data.animal_breed is None
        assert minimal_contract_data.approved_at is None

    def test_frozen_dataclass(self, sample_contract_data: ContractData) -> None:
        with pytest.raises(AttributeError):
            sample_contract_data.adopter_name = "Changed"  # type: ignore[misc]


class TestContractPDFGenerator:
    """Tests for PDF generation."""

    def test_generate_creates_pdf_file(
        self, tmp_path: Path, sample_contract_data: ContractData
    ) -> None:
        generator = ContractPDFGenerator(storage_dir=tmp_path)
        result_path = generator.generate(sample_contract_data)

        assert result_path.exists()
        assert result_path.suffix == ".pdf"
        assert result_path.stat().st_size > 0

    def test_generate_creates_directory_structure(
        self, tmp_path: Path, sample_contract_data: ContractData
    ) -> None:
        generator = ContractPDFGenerator(storage_dir=tmp_path)
        result_path = generator.generate(sample_contract_data)

        expected_dir = tmp_path / str(sample_contract_data.request_id)
        assert expected_dir.is_dir()
        assert result_path == expected_dir / "contract.pdf"

    def test_generate_minimal_data(
        self, tmp_path: Path, minimal_contract_data: ContractData
    ) -> None:
        generator = ContractPDFGenerator(storage_dir=tmp_path)
        result_path = generator.generate(minimal_contract_data)

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_regenerate_overwrites_existing(
        self, tmp_path: Path, sample_contract_data: ContractData
    ) -> None:
        generator = ContractPDFGenerator(storage_dir=tmp_path)

        path1 = generator.generate(sample_contract_data)
        size1 = path1.stat().st_size

        path2 = generator.generate(sample_contract_data)
        size2 = path2.stat().st_size

        assert path1 == path2
        # Sizes should be approximately equal (same data)
        assert abs(size1 - size2) < 100

    def test_pdf_starts_with_pdf_header(
        self, tmp_path: Path, sample_contract_data: ContractData
    ) -> None:
        generator = ContractPDFGenerator(storage_dir=tmp_path)
        result_path = generator.generate(sample_contract_data)

        with open(result_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"


class TestContractPDFGeneratorBytes:
    """Tests for the generate_bytes() method."""

    def test_generate_bytes_returns_bytes(self, sample_contract_data: ContractData) -> None:
        generator = ContractPDFGenerator()
        result = generator.generate_bytes(sample_contract_data)
        assert isinstance(result, bytes)

    def test_generate_bytes_is_valid_pdf(self, sample_contract_data: ContractData) -> None:
        generator = ContractPDFGenerator()
        result = generator.generate_bytes(sample_contract_data)
        assert result[:5] == b"%PDF-"

    def test_generate_bytes_has_content(self, sample_contract_data: ContractData) -> None:
        generator = ContractPDFGenerator()
        result = generator.generate_bytes(sample_contract_data)
        assert len(result) > 1000

    def test_generate_bytes_minimal_data(self, minimal_contract_data: ContractData) -> None:
        generator = ContractPDFGenerator()
        result = generator.generate_bytes(minimal_contract_data)
        assert result[:5] == b"%PDF-"

    def test_generate_bytes_does_not_write_to_disk(
        self, tmp_path: Path, sample_contract_data: ContractData
    ) -> None:
        generator = ContractPDFGenerator(storage_dir=tmp_path)
        generator.generate_bytes(sample_contract_data)
        # No files should be created in the storage dir
        assert not any(tmp_path.iterdir())

    def test_generate_bytes_consistent_with_generate_file(
        self, tmp_path: Path, sample_contract_data: ContractData
    ) -> None:
        generator = ContractPDFGenerator(storage_dir=tmp_path)
        pdf_bytes = generator.generate_bytes(sample_contract_data)
        pdf_path = generator.generate(sample_contract_data)

        with open(pdf_path, "rb") as f:
            file_bytes = f.read()

        # Both should be valid PDFs of similar size (minor timestamp diff allowed)
        assert pdf_bytes[:5] == b"%PDF-"
        assert file_bytes[:5] == b"%PDF-"
        assert abs(len(pdf_bytes) - len(file_bytes)) < 200


class TestCommitmentClauses:
    """Tests for the commitment clauses constant."""

    def test_has_four_clauses(self) -> None:
        assert len(COMMITMENT_CLAUSES) == 4

    def test_clauses_are_in_spanish(self) -> None:
        for clause in COMMITMENT_CLAUSES:
            assert "adoptante" in clause.lower()

    def test_clauses_are_numbered(self) -> None:
        for i, clause in enumerate(COMMITMENT_CLAUSES, start=1):
            assert clause.startswith(f"{i}.")
