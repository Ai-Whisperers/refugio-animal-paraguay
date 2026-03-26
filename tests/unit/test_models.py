"""Unit tests for SQLAlchemy ORM models.

Tests validate:
- Model instantiation with required and optional fields
- Enum values match migration CHECK constraint strings exactly
- Relationship attributes are present on AdoptionRequest
- __init__.py exports all public symbols
"""

from datetime import UTC, date, datetime
from uuid import uuid4

from src.db.models import (
    Adopter,
    AdoptionRequest,
    AdoptionRequestStatus,
    Animal,
    AnimalSpecies,
    AnimalStatus,
)
from src.db.models.adopter import Adopter as _AdopterDirect
from src.db.models.adoption_request import AdoptionRequest as _AdoptionRequestDirect
from src.db.models.animal import Animal as _AnimalDirect


class TestAnimalStatusEnum:
    """AnimalStatus enum values must match migration CHECK constraint exactly."""

    def test_all_status_values_match_migration(self) -> None:
        expected = {
            "intake",
            "quarantine",
            "available",
            "foster",
            "under_treatment",
            "adopted",
            "deceased",
        }
        assert {s.value for s in AnimalStatus} == expected

    def test_status_values_are_strings(self) -> None:
        for status in AnimalStatus:
            assert isinstance(status.value, str)

    def test_status_is_str_subclass(self) -> None:
        # Ensures AnimalStatus values work anywhere a str is expected
        assert AnimalStatus.AVAILABLE == "available"
        assert AnimalStatus.INTAKE == "intake"


class TestAnimalSpeciesEnum:
    """AnimalSpecies enum values must match migration CHECK constraint exactly."""

    def test_all_species_values_match_migration(self) -> None:
        expected = {"dog", "cat", "other"}
        assert {s.value for s in AnimalSpecies} == expected

    def test_species_is_str_subclass(self) -> None:
        assert AnimalSpecies.DOG == "dog"
        assert AnimalSpecies.CAT == "cat"


class TestAdoptionRequestStatusEnum:
    """AdoptionRequestStatus values must match migration CHECK constraint exactly."""

    def test_all_status_values_match_migration(self) -> None:
        expected = {"pending", "approved", "rejected", "cancelled"}
        assert {s.value for s in AdoptionRequestStatus} == expected

    def test_status_is_str_subclass(self) -> None:
        assert AdoptionRequestStatus.PENDING == "pending"
        assert AdoptionRequestStatus.APPROVED == "approved"


class TestAnimalModel:
    """Animal model instantiation and attribute validation."""

    def test_instantiate_with_required_fields(self) -> None:
        animal = Animal(name="Buddy", species="dog", status="available")
        assert animal.name == "Buddy"
        assert animal.species == "dog"
        assert animal.status == "available"

    def test_optional_fields_default_to_none(self) -> None:
        animal = Animal(name="Luna", species="cat", status="intake")
        assert animal.birth_date is None
        assert animal.description is None

    def test_optional_fields_accept_values(self) -> None:
        birth = date(2021, 3, 15)
        animal = Animal(
            name="Max",
            species="dog",
            status="foster",
            birth_date=birth,
            description="Friendly golden mix",
        )
        assert animal.birth_date == birth
        assert animal.description == "Friendly golden mix"

    def test_id_can_be_set_explicitly(self) -> None:
        animal_id = uuid4()
        animal = Animal(id=animal_id, name="Rex", species="dog", status="available")
        assert animal.id == animal_id

    def test_back_reference_attribute_exists(self) -> None:
        animal = Animal(name="Buddy", species="dog", status="available")
        assert hasattr(animal, "adoption_requests")

    def test_tablename(self) -> None:
        assert Animal.__tablename__ == "animals"

    def test_accepts_enum_values_for_status(self) -> None:
        animal = Animal(
            name="Whiskers",
            species=AnimalSpecies.CAT,
            status=AnimalStatus.QUARANTINE,
        )
        assert animal.status == "quarantine"
        assert animal.species == "cat"


class TestAdopterModel:
    """Adopter model instantiation and attribute validation."""

    def test_instantiate_with_required_fields(self) -> None:
        adopter = Adopter(full_name="Juan López", email="juan@example.com")
        assert adopter.full_name == "Juan López"
        assert adopter.email == "juan@example.com"

    def test_optional_fields_default_to_none(self) -> None:
        adopter = Adopter(full_name="María García", email="maria@example.com")
        assert adopter.phone is None
        assert adopter.address is None
        assert adopter.gdpr_consent_at is None
        assert adopter.deleted_at is None

    def test_optional_fields_accept_values(self) -> None:
        consent_at = datetime.now(UTC)
        adopter = Adopter(
            full_name="Ana Martínez",
            email="ana@example.com",
            phone="+595 981 123456",
            address="Asunción, Paraguay",
            gdpr_consent_at=consent_at,
        )
        assert adopter.phone == "+595 981 123456"
        assert adopter.address == "Asunción, Paraguay"
        assert adopter.gdpr_consent_at == consent_at

    def test_deleted_at_supports_soft_delete(self) -> None:
        deleted_at = datetime.now(UTC)
        adopter = Adopter(
            full_name="Test User",
            email="test@example.com",
            deleted_at=deleted_at,
        )
        assert adopter.deleted_at == deleted_at

    def test_back_reference_attribute_exists(self) -> None:
        adopter = Adopter(full_name="Test User", email="t@example.com")
        assert hasattr(adopter, "adoption_requests")

    def test_tablename(self) -> None:
        assert Adopter.__tablename__ == "adopters"


class TestAdoptionRequestModel:
    """AdoptionRequest model instantiation and FK attribute validation."""

    def test_instantiate_with_required_fields(self) -> None:
        animal_id = uuid4()
        adopter_id = uuid4()
        submitted = datetime.now(UTC)

        req = AdoptionRequest(
            animal_id=animal_id,
            adopter_id=adopter_id,
            status="pending",
            submitted_at=submitted,
        )
        assert req.animal_id == animal_id
        assert req.adopter_id == adopter_id
        assert req.status == "pending"
        assert req.submitted_at == submitted

    def test_optional_fields_default_to_none(self) -> None:
        req = AdoptionRequest(
            animal_id=uuid4(),
            adopter_id=uuid4(),
            status="pending",
            submitted_at=datetime.now(UTC),
        )
        assert req.decided_at is None
        assert req.notes is None

    def test_optional_fields_accept_values(self) -> None:
        submitted = datetime.now(UTC)
        decided = datetime.now(UTC)
        req = AdoptionRequest(
            animal_id=uuid4(),
            adopter_id=uuid4(),
            status="approved",
            submitted_at=submitted,
            decided_at=decided,
            notes="Good candidate, has yard.",
        )
        assert req.decided_at == decided
        assert req.notes == "Good candidate, has yard."

    def test_relationship_attributes_exist(self) -> None:
        # Relationship attributes must be present (will be None without a DB session)
        req = AdoptionRequest(
            animal_id=uuid4(),
            adopter_id=uuid4(),
            status="pending",
            submitted_at=datetime.now(UTC),
        )
        assert hasattr(req, "animal")
        assert hasattr(req, "adopter")

    def test_accepts_enum_values_for_status(self) -> None:
        req = AdoptionRequest(
            animal_id=uuid4(),
            adopter_id=uuid4(),
            status=AdoptionRequestStatus.APPROVED,
            submitted_at=datetime.now(UTC),
        )
        assert req.status == "approved"

    def test_tablename(self) -> None:
        assert AdoptionRequest.__tablename__ == "adoption_requests"


class TestModelExports:
    """Verify __init__.py re-exports all public symbols."""

    def test_animal_exported(self) -> None:
        assert Animal is _AnimalDirect

    def test_adopter_exported(self) -> None:
        assert Adopter is _AdopterDirect

    def test_adoption_request_exported(self) -> None:
        assert AdoptionRequest is _AdoptionRequestDirect

    def test_enums_exported(self) -> None:
        # Enum classes are already imported from src.db.models at the module top —
        # their presence in this namespace proves the package exports them correctly.
        assert AnimalStatus is not None
        assert AnimalSpecies is not None
        assert AdoptionRequestStatus is not None
