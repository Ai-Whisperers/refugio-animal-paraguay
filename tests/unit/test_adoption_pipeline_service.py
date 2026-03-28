"""Unit tests for adoption pipeline service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.adoption_pipeline_service import (
    MAX_STAGES,
    NAME_MAX_LENGTH,
    DuplicateStageError,
    InvalidPositionError,
    MaxStagesError,
    PipelineError,
    StageNotFoundError,
    create_stage,
    delete_stage,
    get_stage,
    list_stages,
    reorder_stages,
    toggle_stage,
    update_stage,
    validate_color,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_stage(**overrides):
    """Create a mock AdoptionPipelineStage."""
    now = datetime.now(UTC)
    defaults = {
        "id": uuid4(),
        "name": "Application Review",
        "description": "Review the adoption application",
        "position": 1,
        "is_active": True,
        "requires_approval": True,
        "max_days": None,
        "color": "#3B82F6",
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for pipeline error hierarchy."""

    def test_pipeline_error_base(self) -> None:
        err = PipelineError("test", details="detail")
        assert err.message == "test"
        assert err.details == "detail"

    def test_stage_not_found(self) -> None:
        err = StageNotFoundError("abc-123")
        assert "abc-123" in err.details

    def test_duplicate_stage(self) -> None:
        err = DuplicateStageError("Home Visit")
        assert "Home Visit" in err.details

    def test_max_stages(self) -> None:
        err = MaxStagesError()
        assert str(MAX_STAGES) in err.details

    def test_invalid_position(self) -> None:
        err = InvalidPositionError("out of range")
        assert "out of range" in err.details


# ---------------------------------------------------------------------------
# validate_color
# ---------------------------------------------------------------------------


class TestValidateColor:
    """Tests for color validation."""

    def test_valid_color(self) -> None:
        validate_color("#3B82F6")
        validate_color("#000000")
        validate_color("#FFFFFF")
        validate_color("#abcdef")

    def test_invalid_color_raises(self) -> None:
        with pytest.raises(PipelineError, match="Invalid color"):
            validate_color("not-a-color")

    def test_missing_hash_raises(self) -> None:
        with pytest.raises(PipelineError, match="Invalid color"):
            validate_color("3B82F6")

    def test_short_color_raises(self) -> None:
        with pytest.raises(PipelineError, match="Invalid color"):
            validate_color("#3B8")


# ---------------------------------------------------------------------------
# create_stage
# ---------------------------------------------------------------------------


class TestCreateStage:
    """Tests for create_stage."""

    @pytest.mark.asyncio
    async def test_creates_stage(self) -> None:
        db = AsyncMock()
        # existing name check
        name_result = MagicMock()
        name_result.scalar_one_or_none.return_value = None
        # count check
        count_result = MagicMock()
        count_result.scalar_one.return_value = 3
        # max position check
        max_pos_result = MagicMock()
        max_pos_result.scalar_one.return_value = 3

        db.execute.side_effect = [name_result, count_result, max_pos_result]

        stage = await create_stage(
            name="New Stage",
            description="A new stage",
            db=db,
        )
        assert stage.name == "New Stage"
        assert stage.position == 4
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_name_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PipelineError, match="Invalid name"):
            await create_stage(name="", db=db)

    @pytest.mark.asyncio
    async def test_name_too_long_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PipelineError, match="Invalid name"):
            await create_stage(name="A" * (NAME_MAX_LENGTH + 1), db=db)

    @pytest.mark.asyncio
    async def test_duplicate_name_raises(self) -> None:
        db = AsyncMock()
        existing = _make_stage()
        name_result = MagicMock()
        name_result.scalar_one_or_none.return_value = existing
        db.execute.return_value = name_result

        with pytest.raises(DuplicateStageError):
            await create_stage(name="Application Review", db=db)

    @pytest.mark.asyncio
    async def test_max_stages_raises(self) -> None:
        db = AsyncMock()
        name_result = MagicMock()
        name_result.scalar_one_or_none.return_value = None
        count_result = MagicMock()
        count_result.scalar_one.return_value = MAX_STAGES

        db.execute.side_effect = [name_result, count_result]

        with pytest.raises(MaxStagesError):
            await create_stage(name="Overflow Stage", db=db)

    @pytest.mark.asyncio
    async def test_invalid_max_days_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PipelineError, match="Invalid max_days"):
            await create_stage(name="Stage", max_days=0, db=db)

    @pytest.mark.asyncio
    async def test_invalid_color_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PipelineError, match="Invalid color"):
            await create_stage(name="Stage", color="red", db=db)


# ---------------------------------------------------------------------------
# get_stage
# ---------------------------------------------------------------------------


class TestGetStage:
    """Tests for get_stage."""

    @pytest.mark.asyncio
    async def test_returns_stage(self) -> None:
        stage = _make_stage()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = stage
        db.execute.return_value = mock_result

        result = await get_stage(stage.id, db)
        assert result.id == stage.id

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(StageNotFoundError):
            await get_stage(uuid4(), db)


# ---------------------------------------------------------------------------
# list_stages
# ---------------------------------------------------------------------------


class TestListStages:
    """Tests for list_stages."""

    @pytest.mark.asyncio
    async def test_returns_all(self) -> None:
        stages = [_make_stage(position=i) for i in range(1, 4)]
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = stages
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await list_stages(db)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await list_stages(db)
        assert result == []


# ---------------------------------------------------------------------------
# update_stage
# ---------------------------------------------------------------------------


class TestUpdateStage:
    """Tests for update_stage."""

    @pytest.mark.asyncio
    async def test_updates_name(self) -> None:
        stage = _make_stage()
        db = AsyncMock()
        # get_stage call
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = stage
        # duplicate check
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = None

        db.execute.side_effect = [get_result, dup_result]

        result = await update_stage(
            stage_id=stage.id,
            name="Updated Name",
            db=db,
        )
        assert result.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_duplicate_name_raises(self) -> None:
        stage = _make_stage()
        other = _make_stage(name="Other Stage")
        db = AsyncMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = stage
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = other

        db.execute.side_effect = [get_result, dup_result]

        with pytest.raises(DuplicateStageError):
            await update_stage(
                stage_id=stage.id,
                name="Other Stage",
                db=db,
            )


# ---------------------------------------------------------------------------
# toggle_stage
# ---------------------------------------------------------------------------


class TestToggleStage:
    """Tests for toggle_stage."""

    @pytest.mark.asyncio
    async def test_deactivates_stage(self) -> None:
        stage = _make_stage(is_active=True)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = stage
        db.execute.return_value = mock_result

        result = await toggle_stage(stage_id=stage.id, is_active=False, db=db)
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_activates_stage(self) -> None:
        stage = _make_stage(is_active=False)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = stage
        db.execute.return_value = mock_result

        result = await toggle_stage(stage_id=stage.id, is_active=True, db=db)
        assert result.is_active is True


# ---------------------------------------------------------------------------
# reorder_stages
# ---------------------------------------------------------------------------


class TestReorderStages:
    """Tests for reorder_stages."""

    @pytest.mark.asyncio
    async def test_empty_list_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(PipelineError, match="Empty stage list"):
            await reorder_stages(stage_ids=[], db=db)


# ---------------------------------------------------------------------------
# delete_stage
# ---------------------------------------------------------------------------


class TestDeleteStage:
    """Tests for delete_stage."""

    @pytest.mark.asyncio
    async def test_deletes_stage(self) -> None:
        stage = _make_stage(position=2)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = stage
        db.execute.return_value = mock_result

        await delete_stage(stage_id=stage.id, db=db)
        db.delete.assert_called_once_with(stage)

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(StageNotFoundError):
            await delete_stage(stage_id=uuid4(), db=db)
