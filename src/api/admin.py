"""Admin API endpoints — audit trail viewer and export.

All endpoints require admin role authentication.
"""

import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.service import AuditService
from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.audit import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_ACTION_LENGTH,
    MAX_PAGE_SIZE,
    MAX_RESOURCE_ID_LENGTH,
    MAX_RESOURCE_TYPE_LENGTH,
    AuditLogListResponse,
    AuditLogResponse,
)
from src.schemas.error import AUTHENTICATED_RESPONSES

router = APIRouter(prefix="/admin", tags=["admin"], responses=AUTHENTICATED_RESPONSES)


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List audit log entries with filters",
)
async def list_audit_logs(
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    action: str | None = Query(
        default=None, max_length=MAX_ACTION_LENGTH, description="Filter by action type"
    ),
    resource_type: str | None = Query(
        default=None,
        max_length=MAX_RESOURCE_TYPE_LENGTH,
        description="Filter by resource type",
    ),
    resource_id: str | None = Query(
        default=None, max_length=MAX_RESOURCE_ID_LENGTH, description="Filter by resource ID"
    ),
    start_date: datetime | None = Query(
        default=None, description="Filter entries from this date (inclusive)"
    ),
    end_date: datetime | None = Query(
        default=None, description="Filter entries until this date (inclusive)"
    ),
    page: int = Query(default=DEFAULT_PAGE, ge=1, description="Page number"),
    page_size: int = Query(
        default=DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Items per page",
    ),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> AuditLogListResponse:
    """Return paginated, filtered audit log entries. Admin only."""
    service = AuditService(db)
    entries, total = await service.list_entries(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/audit-logs/export",
    summary="Export audit log entries as CSV",
    response_class=StreamingResponse,
)
async def export_audit_logs(
    user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None, max_length=MAX_ACTION_LENGTH),
    resource_type: str | None = Query(default=None, max_length=MAX_RESOURCE_TYPE_LENGTH),
    resource_id: str | None = Query(default=None, max_length=MAX_RESOURCE_ID_LENGTH),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    format: str = Query(
        default="csv",
        description="Export format: csv or json",
        pattern="^(csv|json)$",
    ),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> StreamingResponse:
    """Export all filtered audit log entries. Admin only."""
    service = AuditService(db)
    entries = await service.list_all_filtered(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
    )

    if format == "json":
        import json

        data = [AuditLogResponse.model_validate(e).model_dump(mode="json") for e in entries]
        content = json.dumps(data, indent=2, default=str)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit-logs.json"},
        )

    # CSV export (default)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "user_id",
            "action",
            "resource_type",
            "resource_id",
            "timestamp",
            "ip_address",
            "user_agent",
            "request_id",
        ]
    )
    for entry in entries:
        writer.writerow(
            [
                str(entry.id),
                str(entry.user_id),
                entry.action,
                entry.resource_type,
                entry.resource_id or "",
                entry.timestamp.isoformat() if entry.timestamp else "",
                entry.ip_address or "",
                entry.user_agent or "",
                entry.request_id or "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-logs.csv"},
    )
