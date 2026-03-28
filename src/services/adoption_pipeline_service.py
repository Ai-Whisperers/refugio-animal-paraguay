"""Adoption pipeline service — manage configurable pipeline stages.

Provides CRUD operations for adoption pipeline stages including
creation, reordering, activation/deactivation, and validation.
"""

import logging
import re
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_pipeline import AdoptionPipelineStage

logger = logging.getLogger(__name__)

# Configuration
NAME_MAX_LENGTH = 100
MAX_STAGES = 20
VALID_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"

# Default stage names for validation
DEFAULT_STAGES = frozenset(
    {
        "Application Review",
        "Home Visit",
        "Trial Period",
        "Final Approval",
        "Completed",
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PipelineError(Exception):
    """Base error for pipeline operations."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class StageNotFoundError(PipelineError):
    """Raised when pipeline stage not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message="Pipeline stage not found",
            details=f"No pipeline stage found for: {identifier}",
        )


class DuplicateStageError(PipelineError):
    """Raised when stage name already exists."""

    def __init__(self, name: str) -> None:
        super().__init__(
            message="Duplicate stage name",
            details=f"A stage with name '{name}' already exists",
        )


class MaxStagesError(PipelineError):
    """Raised when maximum stages reached."""

    def __init__(self) -> None:
        super().__init__(
            message="Maximum stages reached",
            details=f"Cannot have more than {MAX_STAGES} pipeline stages",
        )


class InvalidPositionError(PipelineError):
    """Raised for invalid stage position."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message="Invalid position",
            details=reason,
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_color(color: str) -> None:
    """Validate hex color code."""
    if not re.match(VALID_COLOR_PATTERN, color):
        raise PipelineError(
            "Invalid color",
            details=f"Color must be a valid hex code (e.g., #3B82F6). Got: {color}",
        )


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def create_stage(
    *,
    name: str,
    description: str | None = None,
    requires_approval: bool = True,
    max_days: int | None = None,
    color: str = "#6B7280",
    db: AsyncSession,
) -> AdoptionPipelineStage:
    """Create a new pipeline stage at the end of the pipeline.

    Raises:
        PipelineError: If validation fails.
        DuplicateStageError: If name already exists.
        MaxStagesError: If maximum stages reached.
    """
    if not name or len(name) > NAME_MAX_LENGTH:
        raise PipelineError(
            "Invalid name",
            details=f"Name must be 1-{NAME_MAX_LENGTH} characters",
        )
    if max_days is not None and max_days <= 0:
        raise PipelineError(
            "Invalid max_days",
            details="max_days must be greater than zero",
        )

    validate_color(color)

    # Check for duplicate name
    existing = await db.execute(
        select(AdoptionPipelineStage).where(AdoptionPipelineStage.name == name)
    )
    if existing.scalar_one_or_none() is not None:
        raise DuplicateStageError(name)

    # Check max stages
    count_result = await db.execute(select(func.count()).select_from(AdoptionPipelineStage))
    count = count_result.scalar_one()
    if count >= MAX_STAGES:
        raise MaxStagesError()

    # Get next position
    max_pos_result = await db.execute(
        select(func.coalesce(func.max(AdoptionPipelineStage.position), 0))
    )
    next_position = max_pos_result.scalar_one() + 1

    stage = AdoptionPipelineStage(
        name=name,
        description=description,
        position=next_position,
        requires_approval=requires_approval,
        max_days=max_days,
        color=color,
    )
    db.add(stage)
    await db.flush()

    logger.info(
        "Created pipeline stage: id=%s name=%s position=%d",
        stage.id,
        name,
        next_position,
    )
    return stage


async def get_stage(
    stage_id: UUID,
    db: AsyncSession,
) -> AdoptionPipelineStage:
    """Get a pipeline stage by ID.

    Raises:
        StageNotFoundError: If not found.
    """
    result = await db.execute(
        select(AdoptionPipelineStage).where(AdoptionPipelineStage.id == stage_id)
    )
    stage = result.scalar_one_or_none()
    if stage is None:
        raise StageNotFoundError(str(stage_id))
    return stage


async def list_stages(
    db: AsyncSession,
    *,
    active_only: bool = False,
) -> list[AdoptionPipelineStage]:
    """List all pipeline stages ordered by position."""
    stmt = select(AdoptionPipelineStage).order_by(AdoptionPipelineStage.position)
    if active_only:
        stmt = stmt.where(AdoptionPipelineStage.is_active.is_(True))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_stage(
    *,
    stage_id: UUID,
    name: str | None = None,
    description: str | None = None,
    requires_approval: bool | None = None,
    max_days: int | None = None,
    color: str | None = None,
    db: AsyncSession,
) -> AdoptionPipelineStage:
    """Update a pipeline stage's properties.

    Raises:
        StageNotFoundError: If not found.
        DuplicateStageError: If new name already exists.
        PipelineError: If validation fails.
    """
    stage = await get_stage(stage_id, db)

    if name is not None:
        if not name or len(name) > NAME_MAX_LENGTH:
            raise PipelineError(
                "Invalid name",
                details=f"Name must be 1-{NAME_MAX_LENGTH} characters",
            )
        # Check for duplicate name (excluding self)
        existing = await db.execute(
            select(AdoptionPipelineStage).where(
                AdoptionPipelineStage.name == name,
                AdoptionPipelineStage.id != stage_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise DuplicateStageError(name)
        stage.name = name

    if description is not None:
        stage.description = description

    if requires_approval is not None:
        stage.requires_approval = requires_approval

    if max_days is not None:
        if max_days <= 0:
            raise PipelineError(
                "Invalid max_days",
                details="max_days must be greater than zero",
            )
        stage.max_days = max_days

    if color is not None:
        validate_color(color)
        stage.color = color

    await db.flush()
    logger.info("Updated pipeline stage: id=%s", stage_id)
    return stage


async def toggle_stage(
    *,
    stage_id: UUID,
    is_active: bool,
    db: AsyncSession,
) -> AdoptionPipelineStage:
    """Activate or deactivate a pipeline stage.

    Raises:
        StageNotFoundError: If not found.
    """
    stage = await get_stage(stage_id, db)
    stage.is_active = is_active
    await db.flush()

    logger.info(
        "Toggled pipeline stage: id=%s active=%s",
        stage_id,
        is_active,
    )
    return stage


async def reorder_stages(
    *,
    stage_ids: list[UUID],
    db: AsyncSession,
) -> list[AdoptionPipelineStage]:
    """Reorder pipeline stages by providing the desired order.

    The position of each stage is set to its index + 1 in the list.

    Raises:
        PipelineError: If stage_ids don't match existing stages.
        StageNotFoundError: If any stage not found.
    """
    if not stage_ids:
        raise PipelineError(
            "Empty stage list",
            details="At least one stage ID must be provided",
        )

    # Verify all stages exist
    all_stages = await list_stages(db)
    existing_ids = {s.id for s in all_stages}
    provided_ids = set(stage_ids)

    if provided_ids != existing_ids:
        missing = existing_ids - provided_ids
        extra = provided_ids - existing_ids
        details_parts = []
        if missing:
            details_parts.append(f"Missing: {len(missing)} stage(s)")
        if extra:
            details_parts.append(f"Unknown: {len(extra)} stage(s)")
        raise PipelineError(
            "Stage list mismatch",
            details=". ".join(details_parts),
        )

    # Temporarily set positions to negative to avoid unique constraint
    await db.execute(
        update(AdoptionPipelineStage).values(position=-1 * AdoptionPipelineStage.position)
    )
    await db.flush()

    # Set new positions
    stage_map = {s.id: s for s in all_stages}
    for idx, stage_id in enumerate(stage_ids, start=1):
        stage = stage_map[stage_id]
        stage.position = idx

    await db.flush()

    logger.info("Reordered %d pipeline stages", len(stage_ids))
    return await list_stages(db)


async def delete_stage(
    *,
    stage_id: UUID,
    db: AsyncSession,
) -> None:
    """Delete a pipeline stage and reorder remaining stages.

    Raises:
        StageNotFoundError: If not found.
    """
    stage = await get_stage(stage_id, db)
    deleted_position = stage.position

    await db.delete(stage)
    await db.flush()

    # Reorder remaining stages to fill the gap
    await db.execute(
        update(AdoptionPipelineStage)
        .where(AdoptionPipelineStage.position > deleted_position)
        .values(position=AdoptionPipelineStage.position - 1)
    )
    await db.flush()

    logger.info("Deleted pipeline stage: id=%s position=%d", stage_id, deleted_position)
