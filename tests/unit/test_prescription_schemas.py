"""Unit tests for prescription schemas."""

import uuid
from datetime import date, datetime, timezone

import pytest

from src.db.models.medical import MedicationFrequency, MedicationStatus
from src.schemas.prescriptions import PrescriptionListResponse, PrescriptionRow


def _make_row(**kwargs) -> dict:
    """Return a minimal valid prescription row dict."""
    defaults: dict = {
        "id": uuid.uuid4(),
        "treatment_id": uuid.uuid4(),
        "name": "Amoxicilina",
        "dosage": "250mg",
        "frequency": MedicationFrequency.TWICE_DAILY,
        "route": "oral",
        "start_date": date(2026, 3, 1),
        "end_date": None,
        "medication_status": MedicationStatus.ACTIVE,
        "notes": None,
        "created_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "animal_id": uuid.uuid4(),
        "animal_name": "Luna",
        "animal_species": "dog",
    }
    defaults.update(kwargs)
    return defaults


class TestPrescriptionRow:
    """Tests for PrescriptionRow schema."""

    def test_valid_minimal_row(self) -> None:
        row = PrescriptionRow.model_validate(_make_row())
        assert row.name == "Amoxicilina"
        assert row.animal_name == "Luna"
        assert row.medication_status == MedicationStatus.ACTIVE

    def test_with_end_date(self) -> None:
        row = PrescriptionRow.model_validate(
            _make_row(end_date=date(2026, 4, 1))
        )
        assert row.end_date == date(2026, 4, 1)

    def test_completed_status(self) -> None:
        row = PrescriptionRow.model_validate(
            _make_row(medication_status=MedicationStatus.COMPLETED)
        )
        assert row.medication_status == MedicationStatus.COMPLETED

    def test_discontinued_status(self) -> None:
        row = PrescriptionRow.model_validate(
            _make_row(medication_status=MedicationStatus.DISCONTINUED)
        )
        assert row.medication_status == MedicationStatus.DISCONTINUED

    def test_all_frequency_values(self) -> None:
        for freq in MedicationFrequency:
            row = PrescriptionRow.model_validate(_make_row(frequency=freq))
            assert row.frequency == freq

    def test_nullable_route(self) -> None:
        row = PrescriptionRow.model_validate(_make_row(route=None))
        assert row.route is None

    def test_nullable_notes(self) -> None:
        row = PrescriptionRow.model_validate(_make_row(notes=None))
        assert row.notes is None

    def test_notes_populated(self) -> None:
        row = PrescriptionRow.model_validate(
            _make_row(notes="Administrar con comida")
        )
        assert row.notes == "Administrar con comida"


class TestPrescriptionListResponse:
    """Tests for PrescriptionListResponse schema."""

    def test_empty_list(self) -> None:
        resp = PrescriptionListResponse(items=[], total=0, page=1, page_size=25)
        assert resp.total == 0
        assert resp.items == []

    def test_with_items(self) -> None:
        rows = [
            PrescriptionRow.model_validate(_make_row()),
            PrescriptionRow.model_validate(
                _make_row(name="Ibuprofeno", medication_status=MedicationStatus.COMPLETED)
            ),
        ]
        resp = PrescriptionListResponse(items=rows, total=2, page=1, page_size=25)
        assert resp.total == 2
        assert len(resp.items) == 2
        assert resp.items[0].name == "Amoxicilina"
        assert resp.items[1].name == "Ibuprofeno"

    def test_pagination_fields(self) -> None:
        resp = PrescriptionListResponse(items=[], total=100, page=3, page_size=10)
        assert resp.page == 3
        assert resp.page_size == 10
        assert resp.total == 100
