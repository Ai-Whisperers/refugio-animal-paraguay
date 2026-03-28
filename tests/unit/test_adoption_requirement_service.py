"""Unit tests for adoption requirement service.

Tests requirement creation, validation, merging logic, and
pre-qualification question generation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.adoption_requirement import (
    REQUIREMENT_DESCRIPTIONS,
    AdoptionRequirement,
    RequirementType,
)
from src.services.adoption_requirement_service import (
    InvalidRequirementValueError,
    RequirementNotFoundError,
    create_requirement,
    get_animal_requirements,
    get_pre_qualification_questions,
    soft_delete_requirement,
    update_requirement,
    validate_requirement_value,
)

# --- Helpers ---


def _make_requirement(**overrides) -> MagicMock:
    """Create a mock AdoptionRequirement with defaults."""
    defaults = {
        "id": uuid4(),
        "animal_id": None,
        "requirement_type": RequirementType.YARD_REQUIRED,
        "value": {"yard": "required"},
        "is_mandatory": True,
        "active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    req = MagicMock(spec=AdoptionRequirement)
    for k, v in defaults.items():
        setattr(req, k, v)
    return req


def _mock_db() -> AsyncMock:
    """Create a mock async database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.get = AsyncMock()
    return db


# --- RequirementType Enum Tests ---


class TestRequirementType:
    """Tests for requirement type enum values."""

    def test_all_types_exist(self) -> None:
        assert RequirementType.YARD_REQUIRED == "yard_required"
        assert RequirementType.NO_CHILDREN_UNDER == "no_children_under"
        assert RequirementType.EXPERIENCE_REQUIRED == "experience_required"
        assert RequirementType.HOME_TYPE == "home_type"
        assert RequirementType.MAX_HOURS_ALONE == "max_hours_alone"
        assert RequirementType.OTHER_PETS_OK == "other_pets_ok"
        assert RequirementType.HOUSING_STATUS == "housing_status"
        assert RequirementType.INCOME_REQUIREMENT == "income_requirement"

    def test_descriptions_for_all_types(self) -> None:
        for req_type in RequirementType:
            assert req_type in REQUIREMENT_DESCRIPTIONS


# --- Validation Tests ---


class TestValidateRequirementValue:
    """Tests for requirement value validation."""

    def test_yard_required_valid(self) -> None:
        validate_requirement_value("yard_required", {"yard": "required"})
        validate_requirement_value("yard_required", {"yard": "preferred"})
        validate_requirement_value("yard_required", {"yard": "not_needed"})

    def test_yard_required_invalid(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("yard_required", {"yard": "invalid"})

    def test_no_children_under_valid(self) -> None:
        validate_requirement_value("no_children_under", {"age": 5})
        validate_requirement_value("no_children_under", {"age": 0})
        validate_requirement_value("no_children_under", {"age": 18})

    def test_no_children_under_invalid_negative(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("no_children_under", {"age": -1})

    def test_no_children_under_invalid_too_high(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("no_children_under", {"age": 19})

    def test_no_children_under_invalid_not_int(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("no_children_under", {"age": "five"})

    def test_experience_required_valid(self) -> None:
        validate_requirement_value("experience_required", {"level": "none"})
        validate_requirement_value("experience_required", {"level": "some"})
        validate_requirement_value("experience_required", {"level": "experienced"})

    def test_experience_required_invalid(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("experience_required", {"level": "expert"})

    def test_home_type_valid(self) -> None:
        validate_requirement_value("home_type", {"types": ["apartment"]})
        validate_requirement_value("home_type", {"types": ["house", "farm"]})

    def test_home_type_invalid_empty(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("home_type", {"types": []})

    def test_home_type_invalid_type(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("home_type", {"types": ["mansion"]})

    def test_max_hours_alone_valid(self) -> None:
        validate_requirement_value("max_hours_alone", {"hours": 8})
        validate_requirement_value("max_hours_alone", {"hours": 0})
        validate_requirement_value("max_hours_alone", {"hours": 24})

    def test_max_hours_alone_invalid(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("max_hours_alone", {"hours": 25})

    def test_other_pets_ok_valid(self) -> None:
        validate_requirement_value("other_pets_ok", {"pets": ["cats", "dogs"]})

    def test_other_pets_ok_invalid_type(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("other_pets_ok", {"pets": ["fish"]})

    def test_housing_status_valid(self) -> None:
        validate_requirement_value("housing_status", {"status": "owned"})
        validate_requirement_value("housing_status", {"status": "rented"})

    def test_housing_status_invalid(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("housing_status", {"status": "homeless"})

    def test_income_requirement_valid(self) -> None:
        validate_requirement_value("income_requirement", {"monthly": 50000})
        validate_requirement_value("income_requirement", {"monthly": 0})

    def test_income_requirement_invalid_negative(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("income_requirement", {"monthly": -100})

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("unknown_type", {"key": "value"})

    def test_non_dict_value_raises(self) -> None:
        with pytest.raises(InvalidRequirementValueError):
            validate_requirement_value("yard_required", "not a dict")  # type: ignore[arg-type]


# --- Exception Tests ---


class TestExceptions:
    """Tests for custom exceptions."""

    def test_requirement_not_found(self) -> None:
        rid = uuid4()
        error = RequirementNotFoundError(rid)
        assert error.requirement_id == rid
        assert str(rid) in error.message

    def test_invalid_value_error(self) -> None:
        error = InvalidRequirementValueError("yard_required", "bad value")
        assert error.requirement_type == "yard_required"
        assert "bad value" in error.message


# --- create_requirement ---


class TestCreateRequirement:
    """Tests for requirement creation."""

    @pytest.mark.asyncio
    async def test_creates_global_requirement(self) -> None:
        db = _mock_db()

        # The actual function uses AdoptionRequirement directly
        # We just test it doesn't raise and calls db.add
        await create_requirement(
            db,
            requirement_type="yard_required",
            value={"yard": "required"},
            is_mandatory=True,
            animal_id=None,
        )

        db.add.assert_called_once()
        db.flush.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_creates_animal_specific_requirement(self) -> None:
        db = _mock_db()
        animal_id = uuid4()

        await create_requirement(
            db,
            requirement_type="home_type",
            value={"types": ["house", "farm"]},
            is_mandatory=False,
            animal_id=animal_id,
        )

        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_invalid_value(self) -> None:
        db = _mock_db()

        with pytest.raises(InvalidRequirementValueError):
            await create_requirement(
                db,
                requirement_type="yard_required",
                value={"yard": "invalid"},
            )

        db.add.assert_not_called()


# --- get_requirement ---


class TestGetRequirement:
    """Tests for fetching a single requirement."""

    @pytest.mark.asyncio
    async def test_returns_active_requirement(self) -> None:
        db = _mock_db()
        req = _make_requirement(active=True)
        db.get.return_value = req

        from src.services.adoption_requirement_service import get_requirement

        result = await get_requirement(db, req.id)
        assert result == req

    @pytest.mark.asyncio
    async def test_raises_for_missing(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        from src.services.adoption_requirement_service import get_requirement

        with pytest.raises(RequirementNotFoundError):
            await get_requirement(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_for_inactive(self) -> None:
        db = _mock_db()
        req = _make_requirement(active=False)
        db.get.return_value = req

        from src.services.adoption_requirement_service import get_requirement

        with pytest.raises(RequirementNotFoundError):
            await get_requirement(db, req.id)


# --- update_requirement ---


class TestUpdateRequirement:
    """Tests for updating requirements."""

    @pytest.mark.asyncio
    async def test_updates_value(self) -> None:
        db = _mock_db()
        req = _make_requirement(requirement_type="yard_required")
        db.get.return_value = req

        await update_requirement(db, req.id, value={"yard": "preferred"})

        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_updates_mandatory_flag(self) -> None:
        db = _mock_db()
        req = _make_requirement(is_mandatory=True)
        db.get.return_value = req

        await update_requirement(db, req.id, is_mandatory=False)

        assert req.is_mandatory is False

    @pytest.mark.asyncio
    async def test_rejects_invalid_value_on_update(self) -> None:
        db = _mock_db()
        req = _make_requirement(requirement_type="yard_required")
        db.get.return_value = req

        with pytest.raises(InvalidRequirementValueError):
            await update_requirement(db, req.id, value={"yard": "invalid"})


# --- soft_delete_requirement ---


class TestSoftDeleteRequirement:
    """Tests for soft-deleting requirements."""

    @pytest.mark.asyncio
    async def test_executes_update(self) -> None:
        db = _mock_db()
        req = _make_requirement(active=True)
        db.get.return_value = req

        await soft_delete_requirement(db, req.id)

        db.execute.assert_awaited()
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_raises_for_missing(self) -> None:
        db = _mock_db()
        db.get.return_value = None

        with pytest.raises(RequirementNotFoundError):
            await soft_delete_requirement(db, uuid4())


# --- get_animal_requirements (merge logic) ---


class TestGetAnimalRequirements:
    """Tests for merged requirement fetching."""

    @pytest.mark.asyncio
    async def test_returns_global_when_no_animal_specific(self) -> None:
        db = _mock_db()
        global_req = _make_requirement(requirement_type="yard_required", animal_id=None)

        # First execute: global query
        mock_global = MagicMock()
        mock_global.scalars.return_value.all.return_value = [global_req]
        # Second execute: animal query
        mock_animal = MagicMock()
        mock_animal.scalars.return_value.all.return_value = []
        db.execute.side_effect = [mock_global, mock_animal]

        result = await get_animal_requirements(db, uuid4())

        assert len(result) == 1
        assert result[0].requirement_type == "yard_required"

    @pytest.mark.asyncio
    async def test_animal_specific_overrides_global(self) -> None:
        db = _mock_db()
        animal_id = uuid4()
        global_req = _make_requirement(
            requirement_type="yard_required",
            animal_id=None,
            value={"yard": "required"},
        )
        animal_req = _make_requirement(
            requirement_type="yard_required",
            animal_id=animal_id,
            value={"yard": "not_needed"},
        )

        mock_global = MagicMock()
        mock_global.scalars.return_value.all.return_value = [global_req]
        mock_animal = MagicMock()
        mock_animal.scalars.return_value.all.return_value = [animal_req]
        db.execute.side_effect = [mock_global, mock_animal]

        result = await get_animal_requirements(db, animal_id)

        # Should only have the animal-specific one
        assert len(result) == 1
        assert result[0].value == {"yard": "not_needed"}

    @pytest.mark.asyncio
    async def test_merges_different_types(self) -> None:
        db = _mock_db()
        animal_id = uuid4()
        global_req = _make_requirement(requirement_type="yard_required", animal_id=None)
        animal_req = _make_requirement(
            requirement_type="home_type",
            animal_id=animal_id,
            value={"types": ["house"]},
        )

        mock_global = MagicMock()
        mock_global.scalars.return_value.all.return_value = [global_req]
        mock_animal = MagicMock()
        mock_animal.scalars.return_value.all.return_value = [animal_req]
        db.execute.side_effect = [mock_global, mock_animal]

        result = await get_animal_requirements(db, animal_id)

        # Should have both (different types)
        assert len(result) == 2
        types = {r.requirement_type for r in result}
        assert types == {"yard_required", "home_type"}


# --- get_pre_qualification_questions ---


class TestGetPreQualificationQuestions:
    """Tests for pre-qualification question generation."""

    @pytest.mark.asyncio
    async def test_generates_questions(self) -> None:
        db = _mock_db()
        animal_id = uuid4()
        req = _make_requirement(
            requirement_type="yard_required",
            value={"yard": "required"},
            is_mandatory=True,
            animal_id=None,
        )

        mock_global = MagicMock()
        mock_global.scalars.return_value.all.return_value = [req]
        mock_animal = MagicMock()
        mock_animal.scalars.return_value.all.return_value = []
        db.execute.side_effect = [mock_global, mock_animal]

        questions = await get_pre_qualification_questions(db, animal_id)

        assert len(questions) == 1
        assert questions[0]["requirement_type"] == "yard_required"
        assert questions[0]["is_mandatory"] is True
        assert "human_readable_description" in questions[0]

    @pytest.mark.asyncio
    async def test_empty_when_no_requirements(self) -> None:
        db = _mock_db()

        mock_global = MagicMock()
        mock_global.scalars.return_value.all.return_value = []
        mock_animal = MagicMock()
        mock_animal.scalars.return_value.all.return_value = []
        db.execute.side_effect = [mock_global, mock_animal]

        questions = await get_pre_qualification_questions(db, uuid4())

        assert questions == []
