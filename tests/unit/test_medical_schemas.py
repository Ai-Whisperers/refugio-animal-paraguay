"""Unit tests for src/schemas/medical.py — medical record Pydantic schemas."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.medical import (
    DiagnosisSeverity,
    DocumentType,
    MedicationFrequency,
    MedicationStatus,
    TreatmentStatus,
    VisitStatus,
    VisitType,
)
from src.schemas.medical import (
    DiagnosisCreate,
    DiagnosisUpdate,
    MedicalDocumentCreate,
    MedicationCreate,
    MedicationUpdate,
    TreatmentCreate,
    TreatmentUpdate,
    VetVisitCreate,
    VetVisitListResponse,
    VetVisitResponse,
    VetVisitUpdate,
)

# --- VetVisitCreate ---


class TestVetVisitCreate:
    def test_minimal_valid_payload(self) -> None:
        v = VetVisitCreate(veterinarian_name="Dr. Rodriguez")
        assert v.veterinarian_name == "Dr. Rodriguez"
        assert v.visit_type == VisitType.CHECKUP
        assert v.visit_status == VisitStatus.SCHEDULED
        assert v.visit_date is None
        assert v.reason is None
        assert v.notes is None
        assert v.weight_kg is None
        assert v.temperature_celsius is None
        assert v.next_visit_date is None

    def test_all_fields(self) -> None:
        now = datetime.now(UTC)
        v = VetVisitCreate(
            veterinarian_name="Dr. Rodriguez",
            visit_type=VisitType.EMERGENCY,
            visit_status=VisitStatus.COMPLETED,
            visit_date=now,
            reason="Vomiting and lethargy",
            notes="Administered IV fluids",
            weight_kg=12.5,
            temperature_celsius=39.2,
            next_visit_date=date(2026, 4, 15),
        )
        assert v.visit_type == VisitType.EMERGENCY
        assert v.weight_kg == 12.5
        assert v.temperature_celsius == 39.2

    def test_veterinarian_name_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            VetVisitCreate(veterinarian_name="")

    def test_weight_kg_cannot_be_negative(self) -> None:
        with pytest.raises(ValidationError, match="greater_than_equal"):
            VetVisitCreate(veterinarian_name="Dr. X", weight_kg=-1.0)

    def test_temperature_celsius_out_of_range(self) -> None:
        with pytest.raises(ValidationError, match="less_than_equal"):
            VetVisitCreate(veterinarian_name="Dr. X", temperature_celsius=50.0)

        with pytest.raises(ValidationError, match="greater_than_equal"):
            VetVisitCreate(veterinarian_name="Dr. X", temperature_celsius=20.0)


# --- VetVisitUpdate ---


class TestVetVisitUpdate:
    def test_all_none_is_valid(self) -> None:
        v = VetVisitUpdate()
        assert v.veterinarian_name is None
        assert v.visit_type is None

    def test_partial_update(self) -> None:
        v = VetVisitUpdate(notes="Follow-up needed", weight_kg=15.3)
        assert v.notes == "Follow-up needed"
        assert v.weight_kg == 15.3


# --- DiagnosisCreate ---


class TestDiagnosisCreate:
    def test_minimal_valid_payload(self) -> None:
        d = DiagnosisCreate(condition="Parvovirus")
        assert d.condition == "Parvovirus"
        assert d.severity == DiagnosisSeverity.MODERATE
        assert d.is_chronic is False
        assert d.description is None

    def test_all_fields(self) -> None:
        d = DiagnosisCreate(
            condition="Hip dysplasia",
            description="Bilateral hip joint laxity",
            severity=DiagnosisSeverity.SEVERE,
            is_chronic=True,
        )
        assert d.is_chronic is True
        assert d.severity == DiagnosisSeverity.SEVERE

    def test_condition_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            DiagnosisCreate(condition="")


# --- DiagnosisUpdate ---


class TestDiagnosisUpdate:
    def test_all_none_is_valid(self) -> None:
        d = DiagnosisUpdate()
        assert d.condition is None

    def test_partial_update(self) -> None:
        d = DiagnosisUpdate(severity=DiagnosisSeverity.CRITICAL)
        assert d.severity == DiagnosisSeverity.CRITICAL


# --- TreatmentCreate ---


class TestTreatmentCreate:
    def test_minimal_valid_payload(self) -> None:
        t = TreatmentCreate(name="IV Fluids")
        assert t.name == "IV Fluids"
        assert t.treatment_status == TreatmentStatus.PLANNED
        assert t.start_date is None

    def test_all_fields(self) -> None:
        t = TreatmentCreate(
            name="Antibiotics course",
            description="14-day amoxicillin",
            treatment_status=TreatmentStatus.ACTIVE,
            start_date=date(2026, 3, 27),
            end_date=date(2026, 4, 10),
            notes="Monitor for allergic reaction",
        )
        assert t.treatment_status == TreatmentStatus.ACTIVE

    def test_name_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            TreatmentCreate(name="")


# --- TreatmentUpdate ---


class TestTreatmentUpdate:
    def test_partial_update(self) -> None:
        t = TreatmentUpdate(treatment_status=TreatmentStatus.COMPLETED)
        assert t.treatment_status == TreatmentStatus.COMPLETED


# --- MedicationCreate ---


class TestMedicationCreate:
    def test_minimal_valid_payload(self) -> None:
        m = MedicationCreate(
            name="Amoxicillin",
            dosage="250mg",
            start_date=date(2026, 3, 27),
        )
        assert m.name == "Amoxicillin"
        assert m.dosage == "250mg"
        assert m.frequency == MedicationFrequency.DAILY
        assert m.medication_status == MedicationStatus.ACTIVE

    def test_all_fields(self) -> None:
        m = MedicationCreate(
            name="Metacam",
            dosage="0.1mg/kg",
            frequency=MedicationFrequency.TWICE_DAILY,
            route="oral",
            start_date=date(2026, 3, 27),
            end_date=date(2026, 4, 3),
            medication_status=MedicationStatus.ACTIVE,
            notes="Give with food",
        )
        assert m.frequency == MedicationFrequency.TWICE_DAILY
        assert m.route == "oral"

    def test_name_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            MedicationCreate(name="", dosage="10mg", start_date=date(2026, 3, 27))

    def test_dosage_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            MedicationCreate(name="Test", dosage="", start_date=date(2026, 3, 27))


# --- MedicationUpdate ---


class TestMedicationUpdate:
    def test_partial_update(self) -> None:
        m = MedicationUpdate(medication_status=MedicationStatus.DISCONTINUED)
        assert m.medication_status == MedicationStatus.DISCONTINUED


# --- MedicalDocumentCreate ---


class TestMedicalDocumentCreate:
    def test_minimal_valid_payload(self) -> None:
        d = MedicalDocumentCreate(
            title="Blood work results",
            file_url="https://storage.example.com/docs/bloodwork.pdf",
            file_name="bloodwork.pdf",
        )
        assert d.document_type == DocumentType.OTHER
        assert d.title == "Blood work results"

    def test_all_fields(self) -> None:
        d = MedicalDocumentCreate(
            document_type=DocumentType.LAB_RESULT,
            title="CBC Panel",
            description="Complete blood count",
            file_url="https://storage.example.com/docs/cbc.pdf",
            file_name="cbc.pdf",
            file_size_bytes=125000,
            mime_type="application/pdf",
        )
        assert d.document_type == DocumentType.LAB_RESULT
        assert d.file_size_bytes == 125000

    def test_title_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            MedicalDocumentCreate(
                title="",
                file_url="https://example.com/doc.pdf",
                file_name="doc.pdf",
            )

    def test_negative_file_size_rejected(self) -> None:
        with pytest.raises(ValidationError, match="greater_than_equal"):
            MedicalDocumentCreate(
                title="Test",
                file_url="https://example.com/doc.pdf",
                file_name="doc.pdf",
                file_size_bytes=-100,
            )


# --- Response model tests ---


class TestVetVisitResponse:
    def test_from_dict(self) -> None:
        visit_id = uuid4()
        animal_id = uuid4()
        now = datetime.now(UTC)
        data = {
            "id": visit_id,
            "animal_id": animal_id,
            "veterinarian_name": "Dr. Rodriguez",
            "visit_type": VisitType.CHECKUP,
            "visit_status": VisitStatus.COMPLETED,
            "visit_date": now,
            "reason": "Annual checkup",
            "notes": None,
            "weight_kg": 12.5,
            "temperature_celsius": 38.5,
            "next_visit_date": date(2027, 3, 27),
            "diagnoses": [],
            "medical_documents": [],
            "created_at": now,
            "updated_at": now,
        }
        resp = VetVisitResponse(**data)
        assert resp.id == visit_id
        assert resp.veterinarian_name == "Dr. Rodriguez"


class TestVetVisitListResponse:
    def test_empty_list(self) -> None:
        resp = VetVisitListResponse(items=[], total=0, page=1, page_size=20)
        assert resp.total == 0
        assert len(resp.items) == 0


# --- Model enum tests ---


class TestMedicalEnums:
    def test_visit_type_values(self) -> None:
        assert VisitType.CHECKUP == "checkup"
        assert VisitType.EMERGENCY == "emergency"
        assert VisitType.SURGERY == "surgery"
        assert VisitType.VACCINATION == "vaccination"

    def test_visit_status_values(self) -> None:
        assert VisitStatus.SCHEDULED == "scheduled"
        assert VisitStatus.IN_PROGRESS == "in_progress"
        assert VisitStatus.COMPLETED == "completed"
        assert VisitStatus.CANCELLED == "cancelled"

    def test_diagnosis_severity_values(self) -> None:
        assert DiagnosisSeverity.MILD == "mild"
        assert DiagnosisSeverity.CRITICAL == "critical"

    def test_treatment_status_values(self) -> None:
        assert TreatmentStatus.PLANNED == "planned"
        assert TreatmentStatus.ACTIVE == "active"
        assert TreatmentStatus.COMPLETED == "completed"
        assert TreatmentStatus.DISCONTINUED == "discontinued"

    def test_medication_frequency_values(self) -> None:
        assert MedicationFrequency.ONCE == "once"
        assert MedicationFrequency.DAILY == "daily"
        assert MedicationFrequency.AS_NEEDED == "as_needed"

    def test_medication_status_values(self) -> None:
        assert MedicationStatus.ACTIVE == "active"
        assert MedicationStatus.COMPLETED == "completed"
        assert MedicationStatus.DISCONTINUED == "discontinued"

    def test_document_type_values(self) -> None:
        assert DocumentType.LAB_RESULT == "lab_result"
        assert DocumentType.XRAY == "xray"
        assert DocumentType.PRESCRIPTION == "prescription"
