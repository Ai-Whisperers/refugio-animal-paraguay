"""Service for pre-qualification analytics and attempt tracking.

Records each pre-qualification attempt and provides aggregate statistics
for the admin dashboard: pass/fail rates, common failure reasons,
score distributions, and per-animal breakdown.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.pre_qualification_attempt import (
    PreQualificationAttempt,
    QualificationOutcome,
)
from src.services.pre_qualification_service import PreQualificationResult

logger = logging.getLogger(__name__)

# Score distribution bucket boundaries
SCORE_BUCKETS = [
    (0, 20, "0-20"),
    (21, 40, "21-40"),
    (41, 60, "41-60"),
    (61, 80, "61-80"),
    (81, 100, "81-100"),
]

# Maximum number of top failure reasons to return
MAX_TOP_FAILURES = 10

# Maximum number of top animals to return
MAX_TOP_ANIMALS = 10


async def record_attempt(
    db: AsyncSession,
    animal_id: UUID,
    result: PreQualificationResult,
    user_id: UUID | None = None,
) -> PreQualificationAttempt:
    """Record a pre-qualification attempt for analytics.

    Called after pre_qualify_adopter completes — persists the outcome,
    score, and failure details for aggregate reporting.
    """
    failed_types = [f.requirement_type for f in result.failed_requirements]
    mandatory_count = sum(1 for f in result.failed_requirements if f.is_mandatory)
    preferred_count = len(result.failed_requirements) - mandatory_count

    outcome = (
        QualificationOutcome.QUALIFIED if result.qualified else QualificationOutcome.DISQUALIFIED
    )

    attempt = PreQualificationAttempt(
        animal_id=animal_id,
        user_id=user_id,
        outcome=outcome,
        score=result.score,
        failed_requirement_types=json.dumps(failed_types) if failed_types else None,
        mandatory_failures=mandatory_count,
        preferred_failures=preferred_count,
    )
    db.add(attempt)
    await db.flush()
    return attempt


async def get_analytics(
    db: AsyncSession,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    animal_id: UUID | None = None,
) -> dict:
    """Compute aggregate pre-qualification analytics.

    Returns a dict with:
    - total_attempts: total pre-qualification attempts
    - qualified_count: number that passed
    - disqualified_count: number that failed
    - qualification_rate: percentage that passed (0-100)
    - average_score: mean score across all attempts
    - score_distribution: list of {bucket, count} dicts
    - top_failure_reasons: most common failed requirement types
    - top_animals: animals with the most pre-qualification attempts
    """
    # Base filter
    filters = []
    if date_from is not None:
        filters.append(PreQualificationAttempt.created_at >= date_from)
    if date_to is not None:
        filters.append(PreQualificationAttempt.created_at <= date_to)
    if animal_id is not None:
        filters.append(PreQualificationAttempt.animal_id == animal_id)

    # Total + qualified/disqualified counts
    count_stmt = select(
        func.count().label("total"),
        func.count()
        .filter(PreQualificationAttempt.outcome == QualificationOutcome.QUALIFIED)
        .label("qualified"),
        func.count()
        .filter(PreQualificationAttempt.outcome == QualificationOutcome.DISQUALIFIED)
        .label("disqualified"),
        func.coalesce(func.avg(PreQualificationAttempt.score), 0).label("avg_score"),
    ).where(*filters)

    count_result = await db.execute(count_stmt)
    row = count_result.one()
    total = row.total
    qualified = row.qualified
    disqualified = row.disqualified
    avg_score = round(float(row.avg_score), 1)

    qualification_rate = round((qualified / total) * 100, 1) if total > 0 else 0.0

    # Score distribution buckets
    score_distribution = []
    for low, high, label in SCORE_BUCKETS:
        bucket_stmt = select(func.count()).where(
            PreQualificationAttempt.score >= low,
            PreQualificationAttempt.score <= high,
            *filters,
        )
        bucket_result = await db.execute(bucket_stmt)
        count = bucket_result.scalar_one()
        score_distribution.append({"bucket": label, "count": count})

    # Top failure reasons — aggregate from JSON column
    failure_stmt = select(PreQualificationAttempt.failed_requirement_types).where(
        PreQualificationAttempt.failed_requirement_types.isnot(None),
        *filters,
    )
    failure_result = await db.execute(failure_stmt)
    failure_counter: Counter[str] = Counter()
    for (raw_types,) in failure_result:
        try:
            types = json.loads(raw_types)
            failure_counter.update(types)
        except (json.JSONDecodeError, TypeError):
            continue

    top_failures = [
        {"requirement_type": req_type, "count": count}
        for req_type, count in failure_counter.most_common(MAX_TOP_FAILURES)
    ]

    # Top animals by attempt count
    animal_stmt = (
        select(
            PreQualificationAttempt.animal_id,
            func.count().label("attempt_count"),
            func.count()
            .filter(PreQualificationAttempt.outcome == QualificationOutcome.QUALIFIED)
            .label("qualified_count"),
        )
        .where(*filters)
        .group_by(PreQualificationAttempt.animal_id)
        .order_by(func.count().desc())
        .limit(MAX_TOP_ANIMALS)
    )
    animal_result = await db.execute(animal_stmt)
    top_animals = [
        {
            "animal_id": str(row.animal_id),
            "attempt_count": row.attempt_count,
            "qualified_count": row.qualified_count,
        }
        for row in animal_result
    ]

    return {
        "total_attempts": total,
        "qualified_count": qualified,
        "disqualified_count": disqualified,
        "qualification_rate": qualification_rate,
        "average_score": avg_score,
        "score_distribution": score_distribution,
        "top_failure_reasons": top_failures,
        "top_animals": top_animals,
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
    }
