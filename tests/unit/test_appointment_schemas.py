"""Unit tests for appointment schemas."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.db.models.medical import VisitStatus, VisitType
from src.schemas.appointments import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentRow,
)


def _make_row(**kwargs) -> dict:
    """Return a minimal valid appointment row dict."""
    defaults: dict = {
        "id": uuid.uuid4(),
        "animal_id": uuid.uuid4(),
        "animal_name": "Rex",
        "animal_species": "dog",
        "veterinarian_name": "Dr. Sanchez",
        "visit_type": VisitType.CHECKUP,
        "visit_status": VisitStatus.SCHEDULED,
        "visit_date": datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc),
        "reason": None,
        "notes": None,
        "created_at": datetime(2026, 3, 27, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 3, 27, tzinfo=timezone.utc),
    }
    defaults.update(kwargs)
    return defaults


class TestAppointmentRow:
    """Tests for AppointmentRow schema."""

    def test_valid_minimal_row(self) -> None:
        row = AppointmentRow.model_validate(_make_row())
        assert row.animal_name == "Rex"
        assert row.veterinarian_name == "Dr. Sanchez"
        assert row.visit_status == VisitStatus.SCHEDULED

    def test_all_visit_types(self) -> None:
        for vtype in VisitType:
            row = AppointmentRow.model_validate(_make_row(visit_type=vtype))
            assert row.visit_type == vtype

    def test_reason_populated(self) -> None:
        row = AppointmentRow.model_validate(_make_row(reason="Chequeo anual"))
        assert row.reason == "Chequeo anual"

    def test_nullable_reason(self) -> None:
        row = AppointmentRow.model_validate(_make_row(reason=None))
        assert row.reason is None

    def test_nullable_notes(self) -> None:
        row = AppointmentRow.model_validate(_make_row(notes=None))
        assert row.notes is None


class TestAppointmentCreate:
    """Tests for AppointmentCreate schema."""

    def test_valid_minimal_create(self) -> None:
        data = AppointmentCreate(
            animal_id=uuid.uuid4(),
            veterinarian_name="Dr. Lopez",
            visit_date=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
        )
        assert data.visit_type == VisitType.CHECKUP
        assert data.reason is None

    def test_full_create(self) -> None:
        data = AppointmentCreate(
            animal_id=uuid.uuid4(),
            veterinarian_name="Dr. Martinez",
            visit_type=VisitType.VACCINATION,
            visit_date=datetime(2026, 5, 10, 14, 0, tzinfo=timezone.utc),
            reason="Vacuna anual antirrabica",
        )
        assert data.visit_type == VisitType.VACCINATION
        assert data.reason == "Vacuna anual antirrabica"

    def test_vet_name_required(self) -> None:
        with pytest.raises(ValidationError):
            AppointmentCreate(
                animal_id=uuid.uuid4(),
                veterinarian_name="",
                visit_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
            )

    def test_vet_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            AppointmentCreate(
                animal_id=uuid.uuid4(),
                veterinarian_name="A" * 256,
                visit_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
            )


class TestAppointmentListResponse:
    """Tests for AppointmentListResponse schema."""

    def test_empty_list(self) -> None:
        resp = AppointmentListResponse(items=[], total=0, page=1, page_size=25)
        assert resp.total == 0

    def test_with_items(self) -> None:
        rows = [
            AppointmentRow.model_validate(_make_row()),
            AppointmentRow.model_validate(
                _make_row(animal_name="Milo", visit_type=VisitType.VACCINATION)
            ),
        ]
        resp = AppointmentListResponse(items=rows, total=2, page=1, page_size=25)
        assert len(resp.items) == 2
        assert resp.items[1].animal_name == "Milo"

    def test_pagination_defaults(self) -> None:
        resp = AppointmentListResponse(items=[], total=50, page=2, page_size=10)
        assert resp.page == 2
        assert resp.page_size == 10
