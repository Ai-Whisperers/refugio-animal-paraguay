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
            photos: list = []  # noqa: RUF012
            created_at = now
            updated_at = now

        resp = AnimalResponse.model_validate(_FakeAnimal())
        assert resp.id == uid
        assert resp.name == "Bolt"
        assert resp.species == AnimalSpecies.DOG
        assert resp.status == AnimalStatus.AVAILABLE
