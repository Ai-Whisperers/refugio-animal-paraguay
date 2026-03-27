"""Unit tests for bulk vaccination Pydantic schemas."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.schemas.vaccination import (
    BulkVaccinationCreate,
    BulkVaccinationResponse,
    BulkVaccinationResultItem,
)


class TestBulkVaccinationCreate:
    """Tests for BulkVaccinationCreate schema."""

    def test_valid_minimal(self) -> None:
        animal_id = uuid4()
        vt_id = uuid4()
        schema = BulkVaccinationCreate(
            animal_ids=[animal_id],
            vaccine_type_id=vt_id,
            scheduled_date=date(2026, 4, 1),
        )
        assert schema.animal_ids == [animal_id]
        assert schema.vaccine_type_id == vt_id
        assert schema.vaccination_status == "scheduled"
        assert schema.dose_number == 1

    def test_valid_multiple_animals(self) -> None:
        ids = [uuid4() for _ in range(5)]
        schema = BulkVaccinationCreate(
            animal_ids=ids,
            vaccine_type_id=uuid4(),
            scheduled_date=date(2026, 4, 1),
            administered_date=date(2026, 4, 1),
            administered_by="Dr. Martinez",
            batch_number="LOT-BULK-001",
            vaccination_status="administered",
        )
        assert len(schema.animal_ids) == 5
        assert schema.administered_by == "Dr. Martinez"

    def test_empty_animal_ids_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BulkVaccinationCreate(
                animal_ids=[],
                vaccine_type_id=uuid4(),
                scheduled_date=date(2026, 4, 1),
            )

    def test_too_many_animal_ids_rejected(self) -> None:
        ids = [uuid4() for _ in range(101)]
        with pytest.raises(ValidationError):
            BulkVaccinationCreate(
                animal_ids=ids,
                vaccine_type_id=uuid4(),
                scheduled_date=date(2026, 4, 1),
            )

    def test_zero_dose_number_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BulkVaccinationCreate(
                animal_ids=[uuid4()],
                vaccine_type_id=uuid4(),
                scheduled_date=date(2026, 4, 1),
                dose_number=0,
            )

    def test_max_100_animals_accepted(self) -> None:
        ids = [uuid4() for _ in range(100)]
        schema = BulkVaccinationCreate(
            animal_ids=ids,
            vaccine_type_id=uuid4(),
            scheduled_date=date(2026, 4, 1),
        )
        assert len(schema.animal_ids) == 100


class TestBulkVaccinationResultItem:
    """Tests for BulkVaccinationResultItem schema."""

    def test_success_item(self) -> None:
        item = BulkVaccinationResultItem(
            animal_id=uuid4(),
            vaccination_id=uuid4(),
            success=True,
        )
        assert item.success is True
        assert item.error is None

    def test_failure_item(self) -> None:
        item = BulkVaccinationResultItem(
            animal_id=uuid4(),
            vaccination_id=None,
            success=False,
            error="Animal not found",
        )
        assert item.success is False
        assert item.error == "Animal not found"


class TestBulkVaccinationResponse:
    """Tests for BulkVaccinationResponse schema."""

    def test_all_success(self) -> None:
        results = [
            BulkVaccinationResultItem(
                animal_id=uuid4(), vaccination_id=uuid4(), success=True
            )
            for _ in range(3)
        ]
        resp = BulkVaccinationResponse(
            total_requested=3,
            total_created=3,
            total_failed=0,
            results=results,
        )
        assert resp.total_requested == 3
        assert resp.total_created == 3
        assert resp.total_failed == 0

    def test_partial_failure(self) -> None:
        results = [
            BulkVaccinationResultItem(
                animal_id=uuid4(), vaccination_id=uuid4(), success=True
            ),
            BulkVaccinationResultItem(
                animal_id=uuid4(), vaccination_id=None, success=False, error="Not found"
            ),
        ]
        resp = BulkVaccinationResponse(
            total_requested=2,
            total_created=1,
            total_failed=1,
            results=results,
        )
        assert resp.total_requested == 2
        assert resp.total_created == 1
        assert resp.total_failed == 1

    def test_empty_results(self) -> None:
        resp = BulkVaccinationResponse(
            total_requested=0,
            total_created=0,
            total_failed=0,
            results=[],
        )
        assert resp.results == []
