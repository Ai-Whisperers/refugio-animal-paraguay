"""Unit tests for src/schemas/intake.py and src/db/models/intake.py."""

import logging
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.animal import AnimalSpecies
from src.db.models.intake import IntakeSource, handle_quarantine_trigger
from src.schemas.intake import IntakeCreate, IntakeResponse


class TestIntakeSource:
    def test_all_source_values_exist(self) -> None:
        assert IntakeSource.STRAY == "stray"
        assert IntakeSource.SURRENDER == "surrender"
        assert IntakeSource.RESCUE == "rescue"
        assert IntakeSource.TRANSFER == "transfer"

    def test_source_count(self) -> None:
        assert len(IntakeSource) == 4


class TestIntakeCreate:
    def test_minimal_valid_payload(self) -> None:
        intake = IntakeCreate(name="Firulais", source=IntakeSource.STRAY)
        assert intake.name == "Firulais"
        assert intake.source == IntakeSource.STRAY
        assert intake.species == AnimalSpecies.DOG
        assert intake.requires_quarantine is False
        assert intake.finder_name is None
        assert intake.finder_email is None
        assert intake.finder_phone is None
        assert intake.location_found is None
        assert intake.condition_on_arrival is None
        assert intake.photo_urls == []

    def test_full_stray_intake_payload(self) -> None:
        intake = IntakeCreate(
            name="Rescatado",
            species=AnimalSpecies.DOG,
            source=IntakeSource.STRAY,
            finder_name="Carlos Lopez",
            finder_email="carlos@example.com",
            finder_phone="+595971234567",
            location_found="Plaza de Armas, Asuncion",
            condition_on_arrival="Mild dehydration",
            requires_quarantine=True,
            notes="Found near the market",
            photo_urls=["https://example.com/photo1.jpg"],
        )
        assert intake.finder_name == "Carlos Lopez"
        assert intake.finder_email == "carlos@example.com"
        assert intake.requires_quarantine is True
        assert len(intake.photo_urls) == 1

    def test_surrender_source(self) -> None:
        intake = IntakeCreate(
            name="Michi", source=IntakeSource.SURRENDER, species=AnimalSpecies.CAT
        )
        assert intake.source == IntakeSource.SURRENDER
        assert intake.species == AnimalSpecies.CAT

    def test_rescue_source(self) -> None:
        intake = IntakeCreate(name="Rex", source=IntakeSource.RESCUE)
        assert intake.source == IntakeSource.RESCUE

    def test_transfer_source(self) -> None:
        intake = IntakeCreate(name="Buddy", source=IntakeSource.TRANSFER)
        assert intake.source == IntakeSource.TRANSFER

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            IntakeCreate(source=IntakeSource.STRAY)  # type: ignore[call-arg]

    def test_missing_source_raises(self) -> None:
        with pytest.raises(ValidationError, match="source"):
            IntakeCreate(name="Rex")  # type: ignore[call-arg]

    def test_invalid_source_raises(self) -> None:
        with pytest.raises(ValidationError):
            IntakeCreate(name="Rex", source="found_on_street")  # type: ignore[arg-type]

    def test_name_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            IntakeCreate(name="", source=IntakeSource.STRAY)

    def test_name_too_long_raises(self) -> None:
        with pytest.raises(ValidationError, match="string_too_long"):
            IntakeCreate(name="x" * 256, source=IntakeSource.STRAY)

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError, match="email"):
            IntakeCreate(
                name="Rex",
                source=IntakeSource.STRAY,
                finder_email="not-an-email",
            )

    def test_valid_email_accepted(self) -> None:
        intake = IntakeCreate(
            name="Rex",
            source=IntakeSource.STRAY,
            finder_email="finder@example.com",
        )
        assert intake.finder_email == "finder@example.com"

    def test_finder_name_max_length(self) -> None:
        with pytest.raises(ValidationError, match="string_too_long"):
            IntakeCreate(
                name="Rex",
                source=IntakeSource.STRAY,
                finder_name="x" * 256,
            )

    def test_multiple_photo_urls(self) -> None:
        urls = [f"https://example.com/photo{i}.jpg" for i in range(5)]
        intake = IntakeCreate(name="Rex", source=IntakeSource.STRAY, photo_urls=urls)
        assert len(intake.photo_urls) == 5

    def test_quarantine_default_false(self) -> None:
        intake = IntakeCreate(name="Rex", source=IntakeSource.STRAY)
        assert intake.requires_quarantine is False


class TestIntakeResponse:
    def test_from_orm_attributes(self) -> None:
        now = datetime.now(UTC)
        _animal_id = uuid4()
        _staff_id = uuid4()
        _intake_id = uuid4()

        fake_animal = type(
            "_FakeAnimal",
            (),
            {
                "id": _animal_id,
                "name": "Rex",
                "species": "dog",
                "status": "intake",
                "created_at": now,
            },
        )()

        fake_staff = type(
            "_FakeStaff",
            (),
            {
                "id": _staff_id,
                "email": "staff@refugio.test",
            },
        )()

        fake_intake = type(
            "_FakeIntake",
            (),
            {
                "id": _intake_id,
                "animal_id": _animal_id,
                "source": "stray",
                "finder_name": "Carlos",
                "finder_email": "carlos@example.com",
                "finder_phone": "+595971234567",
                "location_found": "Plaza de Armas",
                "condition_on_arrival": "Good",
                "requires_quarantine": False,
                "intake_date": now,
                "staff_id": _staff_id,
                "notes": None,
                "created_at": now,
                "updated_at": now,
                "animal": fake_animal,
                "staff": fake_staff,
            },
        )()

        resp = IntakeResponse.model_validate(fake_intake)
        assert resp.id == _intake_id
        assert resp.source == IntakeSource.STRAY
        assert resp.animal.name == "Rex"
        assert resp.staff.email == "staff@refugio.test"
        assert resp.requires_quarantine is False


class TestQuarantineTrigger:
    def test_quarantine_logs_when_required(self, caplog: pytest.LogCaptureFixture) -> None:
        _animal_id = uuid4()
        _intake_id = uuid4()

        # Use a plain object to avoid SQLAlchemy instrumentation
        record = type(
            "_FakeIntakeRecord",
            (),
            {
                "id": _intake_id,
                "animal_id": _animal_id,
                "requires_quarantine": True,
            },
        )()

        with caplog.at_level(logging.INFO):
            handle_quarantine_trigger(record)  # type: ignore[arg-type]

        assert "Quarantine flagged" in caplog.text
        assert str(_animal_id) in caplog.text

    def test_no_log_when_quarantine_not_required(self, caplog: pytest.LogCaptureFixture) -> None:
        record = type(
            "_FakeIntakeRecord",
            (),
            {"requires_quarantine": False},
        )()

        with caplog.at_level(logging.INFO):
            handle_quarantine_trigger(record)  # type: ignore[arg-type]

        assert "Quarantine flagged" not in caplog.text
