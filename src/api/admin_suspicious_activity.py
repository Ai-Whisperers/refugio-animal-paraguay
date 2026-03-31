"""Admin endpoint for suspicious activity detection.

Provides a single GET endpoint that scans the audit log for anomalous
patterns within a configurable look-back window and returns a structured
report. Requires admin role.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.services.suspicious_activity_service import (
    DETECTION_WINDOW_MINUTES,
    AlertSeverity,
    AlertType,
    detect_suspicious_activity,
)

router = APIRouter(
    prefix="/admin/security",
    tags=["admin-security"],
    responses=AUTHENTICATED_RESPONSES,
)

MAX_WINDOW_MINUTES = 1440  # 24 hours


class SuspiciousActivityAlertResponse(BaseModel):
    """API representation of a single suspicious-activity alert."""

    alert_type: AlertType
    severity: AlertSeverity
    user_id: str
    count: int
    window_minutes: int
    detected_at: datetime
    description: str
    recent_resource_types: list[str]


class SuspiciousActivityReportResponse(BaseModel):
    """API representation of the suspicious-activity scan report."""

    checked_at: datetime
    window_minutes: int
    alert_count: int
    alerts: list[SuspiciousActivityAlertResponse]


@router.get(
    "/suspicious-activity",
    response_model=SuspiciousActivityReportResponse,
    summary="Detect suspicious activity in audit logs",
    description=(
        "Scans recent audit log entries for anomalous patterns: bulk deletions, "
        "mass exports, GDPR erasure bursts, or high-frequency activity from a "
        "single user. Requires admin role."
    ),
)
async def get_suspicious_activity(
    window_minutes: int = Query(
        default=DETECTION_WINDOW_MINUTES,
        ge=1,
        le=MAX_WINDOW_MINUTES,
        description="Look-back window in minutes (1–1440)",
    ),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> SuspiciousActivityReportResponse:
    """Return a suspicious-activity report for the specified window."""
    report = await detect_suspicious_activity(db, window_minutes=window_minutes)
    return SuspiciousActivityReportResponse(
        checked_at=report.checked_at,
        window_minutes=report.window_minutes,
        alert_count=report.alert_count,
        alerts=[
            SuspiciousActivityAlertResponse(
                alert_type=alert.alert_type,
                severity=alert.severity,
                user_id=str(alert.user_id),
                count=alert.count,
                window_minutes=alert.window_minutes,
                detected_at=alert.detected_at,
                description=alert.description,
                recent_resource_types=alert.recent_resource_types,
            )
            for alert in report.alerts
        ],
    )
