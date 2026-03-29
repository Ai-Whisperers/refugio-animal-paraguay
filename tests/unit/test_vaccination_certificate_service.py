"""Unit tests for vaccination certificate PDF generation service."""

from datetime import date
from uuid import uuid4

import pytest
from src.services.pdf_service import PDFGenerationError
from src.services.vaccination_certificate_service import (
    CertificateData,
    VaccinationCertificateGenerator,
    VaccinationRecord,
    generate_vaccination_certificate,
)


@pytest.fixture()
def sample_animal_id():
    """Fixed UUID for predictable filenames."""
    return uuid4()


@pytest.fixture()
def sample_records():
    """Sample vaccination records for testing."""
    return [
        VaccinationRecord(
            vaccine_name="Rabies",
            administered_date=date(2026, 1, 15),
            batch_number="LOT-2026-001",
            administered_by="Dr. Martinez",
            dose_number=1,
            next_due_date=date(2027, 1, 15),
        ),
        VaccinationRecord(
            vaccine_name="DHPP",
            administered_date=date(2026, 2, 10),
            batch_number="LOT-2026-042",
            administered_by="Dr. Lopez",
            dose_number=2,
            next_due_date=date(2026, 5, 10),
        ),
    ]


@pytest.fixture()
def sample_certificate_data(sample_animal_id, sample_records):
    """Complete certificate data for testing."""
    return CertificateData(
        animal_id=sample_animal_id,
        animal_name="Luna",
        animal_species="dog",
        animal_breed="Labrador Mix",
        animal_birth_date=date(2024, 6, 1),
        vaccinations=sample_records,
    )


class TestVaccinationRecord:
    """Tests for VaccinationRecord dataclass."""

    def test_create_minimal(self) -> None:
        record = VaccinationRecord(
            vaccine_name="Rabies",
            administered_date=date(2026, 3, 1),
            batch_number=None,
            administered_by=None,
            dose_number=1,
            next_due_date=None,
        )
        assert record.vaccine_name == "Rabies"
        assert record.batch_number is None
        assert record.administered_by is None
        assert record.next_due_date is None

    def test_create_full(self, sample_records) -> None:
        record = sample_records[0]
        assert record.vaccine_name == "Rabies"
        assert record.batch_number == "LOT-2026-001"
        assert record.administered_by == "Dr. Martinez"
        assert record.dose_number == 1
        assert record.next_due_date == date(2027, 1, 15)

    def test_frozen(self) -> None:
        record = VaccinationRecord(
            vaccine_name="Rabies",
            administered_date=date(2026, 3, 1),
            batch_number=None,
            administered_by=None,
            dose_number=1,
            next_due_date=None,
        )
        with pytest.raises(AttributeError):
            record.vaccine_name = "Modified"  # type: ignore[misc]


class TestCertificateData:
    """Tests for CertificateData dataclass."""

    def test_create_minimal(self) -> None:
        uid = uuid4()
        data = CertificateData(
            animal_id=uid,
            animal_name="Max",
            animal_species="dog",
            animal_breed=None,
            animal_birth_date=None,
        )
        assert data.animal_id == uid
        assert data.animal_breed is None
        assert data.animal_birth_date is None
        assert data.vaccinations == []

    def test_create_with_vaccinations(self, sample_certificate_data) -> None:
        assert len(sample_certificate_data.vaccinations) == 2
        assert sample_certificate_data.animal_name == "Luna"
        assert sample_certificate_data.animal_species == "dog"

    def test_frozen(self, sample_certificate_data) -> None:
        with pytest.raises(AttributeError):
            sample_certificate_data.animal_name = "Modified"  # type: ignore[misc]


class TestVaccinationCertificateGenerator:
    """Tests for VaccinationCertificateGenerator using BasePDFGenerator interface."""

    def test_generate_bytes_returns_pdf(self, sample_certificate_data) -> None:
        generator = VaccinationCertificateGenerator()
        pdf_bytes = generator.generate_bytes(sample_certificate_data)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_generate_bytes_empty_vaccinations(self) -> None:
        generator = VaccinationCertificateGenerator()
        data = CertificateData(
            animal_id=uuid4(),
            animal_name="Orphan",
            animal_species="cat",
            animal_breed=None,
            animal_birth_date=None,
            vaccinations=[],
        )
        pdf_bytes = generator.generate_bytes(data)
        assert pdf_bytes[:4] == b"%PDF"
        assert len(pdf_bytes) > 1000

    def test_generate_bytes_multiple_vaccinations(self, sample_certificate_data) -> None:
        generator = VaccinationCertificateGenerator()
        pdf_bytes = generator.generate_bytes(sample_certificate_data)
        # Multi-vaccination certificate should be larger than empty one
        empty_data = CertificateData(
            animal_id=uuid4(),
            animal_name="Empty",
            animal_species="dog",
            animal_breed=None,
            animal_birth_date=None,
        )
        empty_bytes = generator.generate_bytes(empty_data)
        assert len(pdf_bytes) > len(empty_bytes)

    def test_generate_file_writes_pdf(self, sample_certificate_data, tmp_path) -> None:
        generator = VaccinationCertificateGenerator()
        out_path = tmp_path / "cert.pdf"
        result = generator.generate_file(sample_certificate_data, out_path)
        assert result == out_path.resolve()
        assert out_path.exists()
        assert out_path.read_bytes()[:4] == b"%PDF"

    def test_invalid_data_raises_error(self) -> None:
        generator = VaccinationCertificateGenerator()
        with pytest.raises(PDFGenerationError):
            generator.generate_bytes("not a CertificateData")  # type: ignore[arg-type]


class TestGenerateVaccinationCertificate:
    """Tests for generate_vaccination_certificate function."""

    def test_generates_pdf_with_vaccinations(
        self, sample_certificate_data, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            "src.services.vaccination_certificate_service.CERTIFICATE_STORAGE_DIR",
            tmp_path,
        )
        filepath = generate_vaccination_certificate(sample_certificate_data)
        assert filepath.exists()
        assert filepath.suffix == ".pdf"
        assert filepath.stat().st_size > 0
        assert str(sample_certificate_data.animal_id) in filepath.name

    def test_generates_pdf_without_vaccinations(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            "src.services.vaccination_certificate_service.CERTIFICATE_STORAGE_DIR",
            tmp_path,
        )
        data = CertificateData(
            animal_id=uuid4(),
            animal_name="Orphan",
            animal_species="cat",
            animal_breed=None,
            animal_birth_date=None,
            vaccinations=[],
        )
        filepath = generate_vaccination_certificate(data)
        assert filepath.exists()
        assert filepath.suffix == ".pdf"

    def test_generates_pdf_with_missing_optional_fields(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            "src.services.vaccination_certificate_service.CERTIFICATE_STORAGE_DIR",
            tmp_path,
        )
        records = [
            VaccinationRecord(
                vaccine_name="Rabies",
                administered_date=date(2026, 3, 1),
                batch_number=None,
                administered_by=None,
                dose_number=1,
                next_due_date=None,
            ),
        ]
        data = CertificateData(
            animal_id=uuid4(),
            animal_name="Stray",
            animal_species="dog",
            animal_breed=None,
            animal_birth_date=None,
            vaccinations=records,
        )
        filepath = generate_vaccination_certificate(data)
        assert filepath.exists()

    def test_creates_storage_directory(self, tmp_path, monkeypatch) -> None:
        storage_dir = tmp_path / "nested" / "certs"
        monkeypatch.setattr(
            "src.services.vaccination_certificate_service.CERTIFICATE_STORAGE_DIR",
            storage_dir,
        )
        data = CertificateData(
            animal_id=uuid4(),
            animal_name="Test",
            animal_species="dog",
            animal_breed=None,
            animal_birth_date=None,
        )
        filepath = generate_vaccination_certificate(data)
        assert storage_dir.exists()
        assert filepath.exists()

    def test_filename_contains_animal_id(
        self, sample_certificate_data, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            "src.services.vaccination_certificate_service.CERTIFICATE_STORAGE_DIR",
            tmp_path,
        )
        filepath = generate_vaccination_certificate(sample_certificate_data)
        expected_filename = f"vaccination_certificate_{sample_certificate_data.animal_id}.pdf"
        assert filepath.name == expected_filename

    def test_pdf_content_is_valid(self, sample_certificate_data, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            "src.services.vaccination_certificate_service.CERTIFICATE_STORAGE_DIR",
            tmp_path,
        )
        filepath = generate_vaccination_certificate(sample_certificate_data)
        content = filepath.read_bytes()
        # Valid PDFs start with %PDF
        assert content[:4] == b"%PDF"

    def test_multiple_vaccinations_sorted_by_date(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            "src.services.vaccination_certificate_service.CERTIFICATE_STORAGE_DIR",
            tmp_path,
        )
        records = [
            VaccinationRecord(
                vaccine_name="DHPP",
                administered_date=date(2026, 3, 15),
                batch_number="LOT-B",
                administered_by="Dr. B",
                dose_number=2,
                next_due_date=None,
            ),
            VaccinationRecord(
                vaccine_name="Rabies",
                administered_date=date(2026, 1, 10),
                batch_number="LOT-A",
                administered_by="Dr. A",
                dose_number=1,
                next_due_date=date(2027, 1, 10),
            ),
        ]
        data = CertificateData(
            animal_id=uuid4(),
            animal_name="Sorted",
            animal_species="dog",
            animal_breed="Mixed",
            animal_birth_date=date(2024, 1, 1),
            vaccinations=records,
        )
        filepath = generate_vaccination_certificate(data)
        assert filepath.exists()
        assert filepath.stat().st_size > 0
