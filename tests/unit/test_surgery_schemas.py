"""Unit tests for surgery Pydantic schemas."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.schemas.surgery import (
    PostOpCheckCreate,
    PostOpCheckResponse,
    PostOpCheckUpdate,
    SurgeryCreate,
    SurgeryListResponse,
    SurgeryResponse,
    SurgeryUpdate,
)

# ---------------------------------------------------------------------------
# Surgery schemas
# ---------------------------------------------------------------------------


class TestSurgeryCreate:
    """Tests for SurgeryCreate schema."""

    def test_valid_minimal(self) -> None:
        schema = SurgeryCreate(
            veterinarian_name="Dr. Martinez",
            scheduled_date=date(2026, 4, 15),
        )
        assert schema.veterinarian_name == "Dr. Martinez"
        assert schema.surgery_type == "other"
        assert schema.surgery_status == "scheduled"
        assert schema.anesthesia_type is None

    def test_valid_full(self) -> None:
        schema = SurgeryCreate(
            surgery_type="spay",
            surgery_status="completed",
            veterinarian_name="Dr. Lopez",
            scheduled_date=date(2026, 4, 15),
            performed_date=date(2026, 4, 15),
            anesthesia_type="general",
            anesthesia_notes="Isoflurane, intubated",
            procedure_description="Standard ovariohysterectomy",
            outcome="successful",
            outcome_notes="Clean procedure, no complications",
            weight_kg=12.5,
            follow_up_date=date(2026, 4, 22),
        )
        assert schema.surgery_type == "spay"
        assert schema.outcome == "successful"
        assert schema.weight_kg == 12.5

    def test_empty_vet_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SurgeryCreate(
                veterinarian_name="",
                scheduled_date=date(2026, 4, 15),
            )

    def test_negative_weight_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SurgeryCreate(
                veterinarian_name="Dr. A",
                scheduled_date=date(2026, 4, 15),
                weight_kg=-1.0,
            )


class TestSurgeryUpdate:
    """Tests for SurgeryUpdate schema."""

    def test_all_none(self) -> None:
        schema = SurgeryUpdate()
        assert schema.surgery_status is None
        assert schema.outcome is None

    def test_partial_update(self) -> None:
        schema = SurgeryUpdate(
            surgery_status="completed",
            outcome="successful",
            performed_date=date(2026, 4, 15),
        )
        assert schema.surgery_status == "completed"
        assert schema.outcome == "successful"


class TestSurgeryResponse:
    """Tests for SurgeryResponse schema."""

    def test_from_dict(self) -> None:
        uid = uuid4()
        animal_id = uuid4()
        now = datetime.now()
        data = {
            "id": uid,
            "animal_id": animal_id,
            "surgery_type": "neuter",
            "surgery_status": "scheduled",
            "veterinarian_name": "Dr. Martinez",
            "scheduled_date": date(2026, 4, 15),
            "performed_date": None,
            "anesthesia_type": None,
            "anesthesia_notes": None,
            "procedure_description": None,
            "outcome": None,
            "outcome_notes": None,
            "complications": None,
            "weight_kg": None,
            "recovery_notes": None,
            "follow_up_date": None,
            "created_at": now,
            "updated_at": now,
        }
        schema = SurgeryResponse.model_validate(data)
        assert schema.id == uid
        assert schema.surgery_type == "neuter"

    def test_list_response(self) -> None:
        resp = SurgeryListResponse(items=[], total=0, page=1, size=20)
        assert resp.total == 0
        assert resp.items == []


# ---------------------------------------------------------------------------
# PostOpCheck schemas
# ---------------------------------------------------------------------------


class TestPostOpCheckCreate:
    """Tests for PostOpCheckCreate schema."""

    def test_valid_minimal(self) -> None:
        schema = PostOpCheckCreate(
            scheduled_time=datetime(2026, 4, 16, 8, 0),
        )
        assert schema.check_status == "pending"
        assert schema.pain_level is None

    def test_valid_full(self) -> None:
        schema = PostOpCheckCreate(
            scheduled_time=datetime(2026, 4, 16, 8, 0),
            check_status="completed",
            completed_time=datetime(2026, 4, 16, 8, 15),
            checked_by="Dr. Martinez",
            temperature_celsius=38.5,
            pain_level=3,
            appetite="normal",
            mobility="limited",
            wound_condition="clean, no swelling",
            notes="Recovering well",
        )
        assert schema.temperature_celsius == 38.5
        assert schema.pain_level == 3

    def test_pain_level_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            PostOpCheckCreate(
                scheduled_time=datetime(2026, 4, 16, 8, 0),
                pain_level=11,
            )

    def test_temperature_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            PostOpCheckCreate(
                scheduled_time=datetime(2026, 4, 16, 8, 0),
                temperature_celsius=50.0,
            )


class TestPostOpCheckUpdate:
    """Tests for PostOpCheckUpdate schema."""

    def test_all_none(self) -> None:
        schema = PostOpCheckUpdate()
        assert schema.check_status is None
        assert schema.pain_level is None

    def test_mark_completed(self) -> None:
        schema = PostOpCheckUpdate(
            check_status="completed",
            completed_time=datetime(2026, 4, 16, 8, 15),
            checked_by="Nurse Garcia",
        )
        assert schema.check_status == "completed"


class TestPostOpCheckResponse:
    """Tests for PostOpCheckResponse schema."""

    def test_from_dict(self) -> None:
        uid = uuid4()
        surgery_id = uuid4()
        now = datetime.now()
        data = {
            "id": uid,
            "surgery_id": surgery_id,
            "check_status": "pending",
            "scheduled_time": now,
            "completed_time": None,
            "checked_by": None,
            "temperature_celsius": None,
            "pain_level": None,
            "appetite": None,
            "mobility": None,
            "wound_condition": None,
            "notes": None,
            "concerns": None,
            "created_at": now,
        }
        schema = PostOpCheckResponse.model_validate(data)
        assert schema.id == uid
        assert schema.check_status == "pending"
