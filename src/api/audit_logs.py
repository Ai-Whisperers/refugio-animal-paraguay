"""Audit log API endpoints for querying and exporting audit trail data.

Endpoints:
  GET  /audit-logs         -- Paginated, filterable audit log listing (admin only)
  GET  /audit-logs/export  -- CSV export of filtered audit logs (admin only)
"""

import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit.service import query_audit_logs
from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.audit_log import AuditLogFilter, AuditLogListResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    action: str | None = Query(default=None, description="Filter by action type"),
    resource_type: str | None = Query(default=None, description="Filter by resource type"),
    resource_id: str | None = Query(default=None, description="Filter by resource ID"),
    date_from: datetime | None = Query(default=None, description="Filter from date (inclusive)"),
    date_to: datetime | None = Query(default=None, description="Filter to date (inclusive)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Items per page"),
) -> AuditLogListResponse:
    """List audit log entries with optional filters. Admin access required."""
    filters = AuditLogFilter(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return await query_audit_logs(db, filters)


@router.get("/export")
async def export_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    user_id: UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> StreamingResponse:
    """Export filtered audit logs as CSV. Admin access required.

    Returns all matching records (no pagination) as a downloadable CSV file.
    """
    # Fetch all matching records (large page size for export)
    filters = AuditLogFilter(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        date_from=date_from,
        date_to=date_to,
        page=1,
        page_size=200,
    )
    result = await query_audit_logs(db, filters)

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
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
            "http_method",
            "path",
            "status_code",
        ]
    )

    # Data rows
    for entry in result.items:
        writer.writerow(
            [
                entry.id,
                str(entry.user_id),
                entry.action,
                entry.resource_type,
                entry.resource_id or "",
                entry.timestamp.isoformat(),
                entry.ip_address or "",
                entry.user_agent or "",
                entry.http_method,
                entry.path,
                entry.status_code,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )
