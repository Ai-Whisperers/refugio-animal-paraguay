"""Unit tests for src/schemas/animal.py."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.animal import AnimalSpecies, AnimalStatus
from src.schemas.animal import AnimalCreate, AnimalResponse, AnimalUpdate


class TestAnimalCreate:
    def test_minimal_valid_payload(self) -> None:
        a = AnimalCreate(name="Buddy")
        assert a.name == "Buddy"
        assert a.species == AnimalSpecies.DOG
        assert a.status == AnimalStatus.INTAKE
        assert a.birth_date is None
        assert a.description is None
        assert a.senacsa_registration_number is None

    def test_all_fields(self) -> None:
        a = AnimalCreate(
            name="Luna",
            species=AnimalSpecies.CAT,
            status=AnimalStatus.AVAILABLE,
            birth_date=date(2022, 6, 1),
            description="Friendly cat",
        )
        assert a.species == AnimalSpecies.CAT
        assert a.status == AnimalStatus.AVAILABLE
        assert a.birth_date == date(2022, 6, 1)

    def test_name_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            AnimalCreate(name="")

    def test_name_cannot_exceed_255_chars(self) -> None:
        with pytest.raises(ValidationError, match="string_too_long"):
            AnimalCreate(name="x" * 256)

    def test_invalid_species_raises(self) -> None:
        with pytest.raises(ValidationError):
            AnimalCreate(name="Rex", species="fish")  # type: ignore[arg-type]

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            AnimalCreate(name="Rex", status="missing")  # type: ignore[arg-type]

    def test_senacsa_registration_number_accepted(self) -> None:
        a = AnimalCreate(name="Rex", senacsa_registration_number="SENACSA-2024-001234")
        assert a.senacsa_registration_number == "SENACSA-2024-001234"

    def test_senacsa_registration_number_max_length(self) -> None:
        with pytest.raises(ValidationError, match="string_too_long"):
            AnimalCreate(name="Rex", senacsa_registration_number="x" * 101)

    def test_senacsa_registration_number_exactly_100_chars_is_valid(self) -> None:
        a = AnimalCreate(name="Rex", senacsa_registration_number="x" * 100)
        assert len(a.senacsa_registration_number) == 100  # type: ignore[arg-type]


class TestAnimalUpdate:
    def test_empty_payload_is_valid(self) -> None:
        u = AnimalUpdate()
        assert u.name is None
        assert u.species is None
        assert u.status is None

    def test_partial_name_only(self) -> None:
        u = AnimalUpdate(name="New Name")
        assert u.name == "New Name"
        assert u.species is None

    def test_model_dump_exclude_unset_only_returns_provided_fields(self) -> None:
        u = AnimalUpdate(status=AnimalStatus.ADOPTED)
        data = u.model_dump(exclude_unset=True)
        assert data == {"status": AnimalStatus.ADOPTED}
        assert "name" not in data

    def test_name_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            AnimalUpdate(name="")

    def test_senacsa_registration_number_can_be_updated(self) -> None:
        u = AnimalUpdate(senacsa_registration_number="PY-2025-999")
        data = u.model_dump(exclude_unset=True)
        assert data == {"senacsa_registration_number": "PY-2025-999"}

    def test_senacsa_registration_number_can_be_cleared(self) -> None:
        # Passing None explicitly removes the registration number
        u = AnimalUpdate(senacsa_registration_number=None)
        data = u.model_dump(exclude_unset=True)
        assert data == {"senacsa_registration_number": None}

    def test_senacsa_registration_number_max_length_on_update(self) -> None:
        with pytest.raises(ValidationError, match="string_too_long"):
            AnimalUpdate(senacsa_registration_number="x" * 101)


class TestAnimalResponse:
    def test_from_orm_attributes(self) -> None:
        now = datetime.now(UTC)
        uid = uuid4()

        class _FakeAnimal:
            id = uid
            name = "Bolt"
            species = "dog"
            status = "available"
            breed = None
            size = None
            gender = None
            birth_date = None
            description = None
            primary_photo_url = None
            senacsa_registration_number = None
            photos: list = []  # noqa: RUF012
            created_at = now
            updated_at = now

        resp = AnimalResponse.model_validate(_FakeAnimal())
        assert resp.id == uid
        assert resp.name == "Bolt"
        assert resp.species == AnimalSpecies.DOG
        assert resp.status == AnimalStatus.AVAILABLE
        assert resp.senacsa_registration_number is None

    def test_senacsa_number_included_in_response(self) -> None:
        now = datetime.now(UTC)
        uid = uuid4()

        class _FakeAnimalWithSenacsa:
            id = uid
            name = "Firulais"
            species = "dog"
            status = "available"
            breed = None
            size = None
            gender = None
            birth_date = None
            description = None
            primary_photo_url = None
            senacsa_registration_number = "SENACSA-2024-005678"
            photos: list = []  # noqa: RUF012
            created_at = now
            updated_at = now

        resp = AnimalResponse.model_validate(_FakeAnimalWithSenacsa())
        assert resp.senacsa_registration_number == "SENACSA-2024-005678"
