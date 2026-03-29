"""Suspicious activity detection service.

Scans the audit log for patterns that may indicate malicious or anomalous
behaviour: bulk deletions, mass exports, repeated GDPR erasures, or
rapid-fire operations from a single user within a short window.

Detection is heuristic — these are signals, not proof of wrongdoing.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# --- Thresholds ---

BULK_DELETE_THRESHOLD = 10
"""Alert when a single user deletes this many resources within the time window."""

BULK_EXPORT_THRESHOLD = 5
"""Alert when a single user performs this many exports within the time window."""

GDPR_ERASURE_THRESHOLD = 3
"""Alert when a single user performs this many GDPR erasures within the time window."""

HIGH_FREQUENCY_THRESHOLD = 50
"""Alert when a single user performs this many total actions within the time window."""

DETECTION_WINDOW_MINUTES = 60
"""Look-back window (minutes) for rate-based detection."""


class AlertSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertType(StrEnum):
    BULK_DELETE = "bulk_delete"
    BULK_EXPORT = "bulk_export"
    GDPR_ERASURE_BURST = "gdpr_erasure_burst"
    HIGH_FREQUENCY_ACTIVITY = "high_frequency_activity"


@dataclass
class SuspiciousActivityAlert:
    """A single suspicious-activity signal."""

    alert_type: AlertType
    severity: AlertSeverity
    user_id: UUID
    count: int
    window_minutes: int
    detected_at: datetime
    description: str
    recent_resource_types: list[str] = field(default_factory=list)


@dataclass
class SuspiciousActivityReport:
    """Summary report returned by the detection API."""

    checked_at: datetime
    window_minutes: int
    alert_count: int
    alerts: list[SuspiciousActivityAlert]


async def detect_suspicious_activity(
    db: AsyncSession,
    *,
    window_minutes: int = DETECTION_WINDOW_MINUTES,
) -> SuspiciousActivityReport:
    """Scan recent audit logs for suspicious patterns.

    Queries aggregate counts per user per action type within the look-back
    window, then applies threshold checks to emit alerts.

    Returns:
        A SuspiciousActivityReport with zero or more alerts.
    """
    now = datetime.now(UTC)
    since = now - timedelta(minutes=window_minutes)

    alerts: list[SuspiciousActivityAlert] = []

    # --- 1. Bulk deletes ---
    delete_query = (
        select(AuditLog.user_id, func.count().label("cnt"))
        .where(AuditLog.action == "delete")
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.user_id)
        .having(func.count() >= BULK_DELETE_THRESHOLD)
    )
    delete_result = await db.execute(delete_query)
    for row in delete_result.fetchall():
        resource_types = await _recent_resource_types(
            db, user_id=row.user_id, action="delete", since=since
        )
        alerts.append(
            SuspiciousActivityAlert(
                alert_type=AlertType.BULK_DELETE,
                severity=AlertSeverity.HIGH,
                user_id=row.user_id,
                count=row.cnt,
                window_minutes=window_minutes,
                detected_at=now,
                description=(
                    f"User performed {row.cnt} delete operations "
                    f"in the last {window_minutes} minutes "
                    f"(threshold: {BULK_DELETE_THRESHOLD})."
                ),
                recent_resource_types=resource_types,
            )
        )

    # --- 2. Bulk exports ---
    export_query = (
        select(AuditLog.user_id, func.count().label("cnt"))
        .where(AuditLog.action == "export")
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.user_id)
        .having(func.count() >= BULK_EXPORT_THRESHOLD)
    )
    export_result = await db.execute(export_query)
    for row in export_result.fetchall():
        resource_types = await _recent_resource_types(
            db, user_id=row.user_id, action="export", since=since
        )
        alerts.append(
            SuspiciousActivityAlert(
                alert_type=AlertType.BULK_EXPORT,
                severity=AlertSeverity.MEDIUM,
                user_id=row.user_id,
                count=row.cnt,
                window_minutes=window_minutes,
                detected_at=now,
                description=(
                    f"User performed {row.cnt} export operations "
                    f"in the last {window_minutes} minutes "
                    f"(threshold: {BULK_EXPORT_THRESHOLD})."
                ),
                recent_resource_types=resource_types,
            )
        )

    # --- 3. GDPR erasure burst ---
    gdpr_query = (
        select(AuditLog.user_id, func.count().label("cnt"))
        .where(AuditLog.action == "gdpr_erasure")
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.user_id)
        .having(func.count() >= GDPR_ERASURE_THRESHOLD)
    )
    gdpr_result = await db.execute(gdpr_query)
    for row in gdpr_result.fetchall():
        alerts.append(
            SuspiciousActivityAlert(
                alert_type=AlertType.GDPR_ERASURE_BURST,
                severity=AlertSeverity.HIGH,
                user_id=row.user_id,
                count=row.cnt,
                window_minutes=window_minutes,
                detected_at=now,
                description=(
                    f"User performed {row.cnt} GDPR erasure operations "
                    f"in the last {window_minutes} minutes "
                    f"(threshold: {GDPR_ERASURE_THRESHOLD}). "
                    "Manual review required."
                ),
                recent_resource_types=[],
            )
        )

    # --- 4. High-frequency activity ---
    freq_query = (
        select(AuditLog.user_id, func.count().label("cnt"))
        .where(AuditLog.timestamp >= since)
        .group_by(AuditLog.user_id)
        .having(func.count() >= HIGH_FREQUENCY_THRESHOLD)
    )
    freq_result = await db.execute(freq_query)
    # Only emit this if not already flagged for bulk_delete (subset)
    flagged_users = {a.user_id for a in alerts if a.alert_type == AlertType.BULK_DELETE}
    for row in freq_result.fetchall():
        if row.user_id in flagged_users:
            continue
        resource_types = await _recent_resource_types(
            db, user_id=row.user_id, action=None, since=since
        )
        alerts.append(
            SuspiciousActivityAlert(
                alert_type=AlertType.HIGH_FREQUENCY_ACTIVITY,
                severity=AlertSeverity.LOW,
                user_id=row.user_id,
                count=row.cnt,
                window_minutes=window_minutes,
                detected_at=now,
                description=(
                    f"User performed {row.cnt} total actions "
                    f"in the last {window_minutes} minutes "
                    f"(threshold: {HIGH_FREQUENCY_THRESHOLD})."
                ),
                recent_resource_types=resource_types,
            )
        )

    if alerts:
        logger.warning(
            "Suspicious activity detected: %d alert(s) in the last %dm window",
            len(alerts),
            window_minutes,
        )

    return SuspiciousActivityReport(
        checked_at=now,
        window_minutes=window_minutes,
        alert_count=len(alerts),
        alerts=alerts,
    )


async def _recent_resource_types(
    db: AsyncSession,
    *,
    user_id: UUID,
    action: str | None,
    since: datetime,
    limit: int = 5,
) -> list[str]:
    """Return the distinct resource types a user touched recently."""
    query = (
        select(AuditLog.resource_type)
        .where(AuditLog.user_id == user_id)
        .where(AuditLog.timestamp >= since)
    )
    if action is not None:
        query = query.where(AuditLog.action == action)
    query = query.distinct().limit(limit)
    result = await db.execute(query)
    return [row[0] for row in result.fetchall()]
