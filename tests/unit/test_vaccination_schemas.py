"""Unit tests for vaccination Pydantic schemas."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.schemas.vaccination import (
    VaccinationCreate,
    VaccinationListResponse,
    VaccinationResponse,
    VaccinationScheduleCreate,
    VaccinationScheduleResponse,
    VaccinationScheduleUpdate,
    VaccinationUpdate,
    VaccineTypeCreate,
    VaccineTypeListResponse,
    VaccineTypeResponse,
    VaccineTypeUpdate,
)

# ---------------------------------------------------------------------------
# VaccineType schemas
# ---------------------------------------------------------------------------


class TestVaccineTypeCreate:
    """Tests for VaccineTypeCreate schema."""

    def test_valid_minimal(self) -> None:
        schema = VaccineTypeCreate(name="Rabies")
        assert schema.name == "Rabies"
        assert schema.target_species == "dog"
        assert schema.is_required is False
        assert schema.description is None
        assert schema.manufacturer is None

    def test_valid_full(self) -> None:
        schema = VaccineTypeCreate(
            name="DHPP",
            description="Distemper, Hepatitis, Parainfluenza, Parvovirus",
            manufacturer="Nobivac",
            target_species="dog",
            is_required=True,
        )
        assert schema.name == "DHPP"
        assert schema.manufacturer == "Nobivac"
        assert schema.is_required is True

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            VaccineTypeCreate(name="")
        assert "min_length" in str(exc_info.value).lower() or "string_too_short" in str(exc_info.value).lower()

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            VaccineTypeCreate(name="A" * 256)


class TestVaccineTypeUpdate:
    """Tests for VaccineTypeUpdate schema."""

    def test_all_none(self) -> None:
        schema = VaccineTypeUpdate()
        assert schema.name is None
        assert schema.is_required is None

    def test_partial_update(self) -> None:
        schema = VaccineTypeUpdate(name="Updated Rabies", is_required=True)
        assert schema.name == "Updated Rabies"
        assert schema.is_required is True
        assert schema.manufacturer is None


class TestVaccineTypeResponse:
    """Tests for VaccineTypeResponse schema."""

    def test_from_attributes(self) -> None:
        uid = uuid4()
        now = datetime.now()

        class FakeORM:
            id = uid
            name = "Rabies"
            description = "Anti-rabies vaccine"
            manufacturer = "MSD"
            target_species = "all"
            is_required = True
            created_at = now

        schema = VaccineTypeResponse.model_validate(FakeORM())
        assert schema.id == uid
        assert schema.name == "Rabies"
        assert schema.is_required is True

    def test_list_response(self) -> None:
        resp = VaccineTypeListResponse(items=[], total=0, page=1, size=20)
        assert resp.total == 0
        assert resp.items == []


# ---------------------------------------------------------------------------
# VaccinationSchedule schemas
# ---------------------------------------------------------------------------


class TestVaccinationScheduleCreate:
    """Tests for VaccinationScheduleCreate schema."""

    def test_valid_minimal(self) -> None:
        vt_id = uuid4()
        schema = VaccinationScheduleCreate(
            vaccine_type_id=vt_id,
            species="dog",
        )
        assert schema.vaccine_type_id == vt_id
        assert schema.dose_number == 1
        assert schema.is_booster is False

    def test_valid_full(self) -> None:
        vt_id = uuid4()
        schema = VaccinationScheduleCreate(
            vaccine_type_id=vt_id,
            species="cat",
            dose_number=2,
            age_weeks_min=8,
            age_weeks_max=12,
            interval_days=28,
            is_booster=True,
            notes="Second dose after 4 weeks",
        )
        assert schema.dose_number == 2
        assert schema.interval_days == 28
        assert schema.is_booster is True

    def test_negative_dose_number_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            VaccinationScheduleCreate(
                vaccine_type_id=uuid4(),
                species="dog",
                dose_number=0,
            )
        assert "greater_than_equal" in str(exc_info.value).lower()

    def test_negative_age_weeks_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VaccinationScheduleCreate(
                vaccine_type_id=uuid4(),
                species="dog",
                age_weeks_min=-1,
            )

    def test_empty_species_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VaccinationScheduleCreate(
                vaccine_type_id=uuid4(),
                species="",
            )


class TestVaccinationScheduleUpdate:
    """Tests for VaccinationScheduleUpdate schema."""

    def test_all_none(self) -> None:
        schema = VaccinationScheduleUpdate()
        assert schema.species is None
        assert schema.dose_number is None

    def test_partial_update(self) -> None:
        schema = VaccinationScheduleUpdate(interval_days=14, is_booster=True)
        assert schema.interval_days == 14
        assert schema.is_booster is True


class TestVaccinationScheduleResponse:
    """Tests for VaccinationScheduleResponse schema."""

    def test_from_attributes(self) -> None:
        uid = uuid4()
        vt_id = uuid4()
        now = datetime.now()

        class FakeORM:
            id = uid
            vaccine_type_id = vt_id
            species = "dog"
            dose_number = 1
            age_weeks_min = 8
            age_weeks_max = 12
            interval_days = None
            is_booster = False
            notes = None
            created_at = now

        schema = VaccinationScheduleResponse.model_validate(FakeORM())
        assert schema.id == uid
        assert schema.species == "dog"


# ---------------------------------------------------------------------------
# Vaccination schemas
# ---------------------------------------------------------------------------


class TestVaccinationCreate:
    """Tests for VaccinationCreate schema."""

    def test_valid_minimal(self) -> None:
        vt_id = uuid4()
        schema = VaccinationCreate(
            vaccine_type_id=vt_id,
            scheduled_date=date(2026, 4, 15),
        )
        assert schema.vaccine_type_id == vt_id
        assert schema.vaccination_status == "scheduled"
        assert schema.dose_number == 1
        assert schema.administered_date is None

    def test_valid_administered(self) -> None:
        vt_id = uuid4()
        schema = VaccinationCreate(
            vaccine_type_id=vt_id,
            scheduled_date=date(2026, 4, 15),
            administered_date=date(2026, 4, 15),
            administered_by="Dr. Martinez",
            batch_number="LOT-2026-001",
            vaccination_status="administered",
            next_due_date=date(2027, 4, 15),
        )
        assert schema.vaccination_status == "administered"
        assert schema.administered_by == "Dr. Martinez"
        assert schema.batch_number == "LOT-2026-001"

    def test_zero_dose_number_rejected(self) -> None:
        with pytest.raises(ValidationError):
            VaccinationCreate(
                vaccine_type_id=uuid4(),
                scheduled_date=date(2026, 4, 15),
                dose_number=0,
            )


class TestVaccinationUpdate:
    """Tests for VaccinationUpdate schema."""

    def test_all_none(self) -> None:
        schema = VaccinationUpdate()
        assert schema.vaccination_status is None
        assert schema.administered_date is None

    def test_mark_administered(self) -> None:
        schema = VaccinationUpdate(
            vaccination_status="administered",
            administered_date=date(2026, 4, 15),
            administered_by="Dr. Lopez",
            batch_number="LOT-2026-002",
            next_due_date=date(2027, 4, 15),
        )
        assert schema.vaccination_status == "administered"
        assert schema.administered_by == "Dr. Lopez"


class TestVaccinationResponse:
    """Tests for VaccinationResponse schema."""

    def test_from_attributes(self) -> None:
        uid = uuid4()
        animal_id = uuid4()
        vt_id = uuid4()
        now = datetime.now()

        class FakeORM:
            id = uid
            animal_id_val = animal_id
            vaccine_type_id_val = vt_id
            vaccination_status = "scheduled"
            scheduled_date = date(2026, 4, 15)
            administered_date = None
            administered_by = None
            batch_number = None
            dose_number = 1
            next_due_date = None
            notes = None
            created_at = now
            updated_at = now
            vaccine_type = None

        # Use dict to avoid attribute name conflicts
        data = {
            "id": uid,
            "animal_id": animal_id,
            "vaccine_type_id": vt_id,
            "vaccination_status": "scheduled",
            "scheduled_date": date(2026, 4, 15),
            "administered_date": None,
            "administered_by": None,
            "batch_number": None,
            "dose_number": 1,
            "next_due_date": None,
            "notes": None,
            "created_at": now,
            "updated_at": now,
            "vaccine_type": None,
        }
        schema = VaccinationResponse.model_validate(data)
        assert schema.id == uid
        assert schema.animal_id == animal_id
        assert schema.vaccination_status == "scheduled"

    def test_list_response(self) -> None:
        resp = VaccinationListResponse(items=[], total=0, page=1, size=20)
        assert resp.total == 0
        assert resp.items == []


class TestVaccinationResponseWithNestedType:
    """Tests for VaccinationResponse with nested VaccineTypeResponse."""

    def test_with_vaccine_type(self) -> None:
        uid = uuid4()
        animal_id = uuid4()
        vt_id = uuid4()
        now = datetime.now()
        data = {
            "id": uid,
            "animal_id": animal_id,
            "vaccine_type_id": vt_id,
            "vaccination_status": "administered",
            "scheduled_date": date(2026, 4, 15),
            "administered_date": date(2026, 4, 15),
            "administered_by": "Dr. Martinez",
            "batch_number": "LOT-001",
            "dose_number": 1,
            "next_due_date": date(2027, 4, 15),
            "notes": "No adverse reactions",
            "created_at": now,
            "updated_at": now,
            "vaccine_type": {
                "id": vt_id,
                "name": "Rabies",
                "description": "Anti-rabies vaccine",
                "manufacturer": "MSD",
                "target_species": "all",
                "is_required": True,
                "created_at": now,
            },
        }
        schema = VaccinationResponse.model_validate(data)
        assert schema.vaccine_type is not None
        assert schema.vaccine_type.name == "Rabies"
        assert schema.vaccination_status == "administered"
