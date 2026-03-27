"""Post-operative monitoring checklist generation service.

Generates a standard set of post-op check-in records based on surgery type.
Each surgery type has a predefined schedule of monitoring intervals.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.surgery import PostOpCheck, Surgery

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Post-op check schedule templates by surgery type
# ---------------------------------------------------------------------------

# Each entry is (hours_after_surgery, label)
# Intervals are measured from the surgery performed_date at 08:00 local time

STANDARD_CHECK_INTERVALS: dict[str, list[tuple[int, str]]] = {
    "spay": [
        (2, "Immediate post-op: vitals, consciousness"),
        (6, "6-hour check: pain, mobility, wound"),
        (24, "Day 1: appetite, elimination, wound"),
        (48, "Day 2: pain level, activity, wound"),
        (72, "Day 3: wound healing, suture check"),
        (168, "Day 7: suture removal assessment"),
        (336, "Day 14: final healing check"),
    ],
    "neuter": [
        (2, "Immediate post-op: vitals, consciousness"),
        (6, "6-hour check: pain, mobility, wound"),
        (24, "Day 1: appetite, elimination, wound"),
        (48, "Day 2: pain level, activity"),
        (168, "Day 7: suture removal assessment"),
        (336, "Day 14: final healing check"),
    ],
    "mass_removal": [
        (2, "Immediate post-op: vitals, consciousness"),
        (6, "6-hour check: pain, bleeding, wound"),
        (24, "Day 1: appetite, wound drainage"),
        (48, "Day 2: wound check, pain level"),
        (72, "Day 3: wound healing progress"),
        (168, "Day 7: suture check, pathology follow-up"),
        (336, "Day 14: final healing, pathology results"),
    ],
    "orthopedic": [
        (2, "Immediate post-op: vitals, consciousness"),
        (4, "4-hour check: limb perfusion, pain"),
        (8, "8-hour check: swelling, pain management"),
        (24, "Day 1: mobility assessment, appetite"),
        (48, "Day 2: swelling, weight bearing"),
        (72, "Day 3: physiotherapy assessment"),
        (168, "Day 7: wound, mobility progress"),
        (336, "Day 14: suture removal, X-ray follow-up"),
        (672, "Day 28: recovery milestone"),
    ],
    "dental": [
        (2, "Immediate post-op: vitals, consciousness"),
        (6, "6-hour check: oral bleeding, pain"),
        (24, "Day 1: eating assessment, pain level"),
        (72, "Day 3: oral healing check"),
        (168, "Day 7: final oral assessment"),
    ],
    "emergency": [
        (1, "1-hour post-op: critical vitals"),
        (2, "2-hour check: stability assessment"),
        (4, "4-hour check: vitals trend"),
        (8, "8-hour check: stabilization"),
        (12, "12-hour check: overnight plan"),
        (24, "Day 1: recovery assessment"),
        (48, "Day 2: progress evaluation"),
        (72, "Day 3: recovery milestone"),
        (168, "Day 7: recovery progress"),
    ],
}

# Default schedule for surgery types not explicitly listed
DEFAULT_CHECK_INTERVALS: list[tuple[int, str]] = [
    (2, "Immediate post-op: vitals, consciousness"),
    (6, "6-hour check: pain, wound"),
    (24, "Day 1: general assessment"),
    (48, "Day 2: recovery check"),
    (168, "Day 7: follow-up assessment"),
]


@dataclass(frozen=True)
class ChecklistGenerationResult:
    """Result of generating a post-op checklist."""

    surgery_id: UUID
    checks_created: int
    check_ids: list[UUID]


async def generate_post_op_checklist(
    surgery_id: UUID,
    db: AsyncSession,
    *,
    base_time: datetime | None = None,
) -> ChecklistGenerationResult:
    """Generate post-op monitoring checks for a surgery.

    Creates PostOpCheck records based on the surgery type's standard
    monitoring schedule. Uses the surgery's performed_date (or scheduled_date
    as fallback) at 08:00 UTC as the base time for scheduling.

    Args:
        surgery_id: The surgery to generate checks for.
        db: Async database session.
        base_time: Override base time for scheduling (useful for testing).

    Returns:
        ChecklistGenerationResult with count and IDs of created checks.

    Raises:
        ValueError: If the surgery is not found.
    """
    result = await db.execute(sa.select(Surgery).where(Surgery.id == surgery_id))
    surgery = result.scalar_one_or_none()
    if surgery is None:
        raise ValueError(f"Surgery {surgery_id} not found")

    # Determine base time for scheduling
    if base_time is None:
        ref_date = surgery.performed_date or surgery.scheduled_date
        base_time = datetime(
            ref_date.year, ref_date.month, ref_date.day,
            8, 0, 0, tzinfo=UTC,
        )

    # Get the check intervals for this surgery type
    intervals = STANDARD_CHECK_INTERVALS.get(
        surgery.surgery_type, DEFAULT_CHECK_INTERVALS
    )

    check_ids: list[UUID] = []
    for hours_offset, notes in intervals:
        scheduled_time = base_time + timedelta(hours=hours_offset)
        check = PostOpCheck(
            surgery_id=surgery_id,
            check_status="pending",
            scheduled_time=scheduled_time,
            notes=notes,
        )
        db.add(check)
        await db.flush()
        check_ids.append(check.id)

    await db.commit()

    logger.info(
        "Generated %d post-op checks for surgery %s (type: %s)",
        len(check_ids),
        surgery_id,
        surgery.surgery_type,
    )

    return ChecklistGenerationResult(
        surgery_id=surgery_id,
        checks_created=len(check_ids),
        check_ids=check_ids,
    )
