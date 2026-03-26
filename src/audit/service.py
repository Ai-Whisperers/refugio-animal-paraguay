"""Audit trail service — records and queries audit log entries.

The service provides:
  - record_audit(): fire-and-forget audit log insertion
  - AuditService: query methods for admin audit endpoints (list, count, export)
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


async def record_audit(
    db: AsyncSession,
    *,
    user_id: UUID,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    request_id: str | None = None,
) -> None:
    """Insert a single audit log entry.

    This is the primary interface for recording audit events. Route handlers
    and middleware call this after a successful operation.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=ip_address,
        user_agent=user_agent,
        old_values=old_values,
        new_values=new_values,
        request_id=request_id,
    )
    db.add(entry)
    await db.flush()
    logger.debug(
        "Audit entry recorded: user=%s action=%s resource=%s/%s",
        user_id,
        action,
        resource_type,
        resource_id,
    )


class AuditService:
    """Query service for audit log entries. Used by admin endpoints."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_entries(
        self,
        *,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Return filtered, paginated audit log entries and total count.

        Returns:
            Tuple of (entries, total_count).
        """
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        # Apply filters
        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action is not None:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)
        if resource_type is not None:
            query = query.where(AuditLog.resource_type == resource_type)
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            query = query.where(AuditLog.resource_id == resource_id)
            count_query = count_query.where(AuditLog.resource_id == resource_id)
        if start_date is not None:
            query = query.where(AuditLog.timestamp >= start_date)
            count_query = count_query.where(AuditLog.timestamp >= start_date)
        if end_date is not None:
            query = query.where(AuditLog.timestamp <= end_date)
            count_query = count_query.where(AuditLog.timestamp <= end_date)

        # Pagination
        offset = (page - 1) * page_size
        query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size)

        result = await self._db.execute(query)
        entries = list(result.scalars().all())

        count_result = await self._db.execute(count_query)
        total = count_result.scalar() or 0

        return entries, total

    async def list_all_filtered(
        self,
        *,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[AuditLog]:
        """Return all filtered entries without pagination (for export)."""
        query = select(AuditLog)

        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
        if action is not None:
            query = query.where(AuditLog.action == action)
        if resource_type is not None:
            query = query.where(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            query = query.where(AuditLog.resource_id == resource_id)
        if start_date is not None:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date is not None:
            query = query.where(AuditLog.timestamp <= end_date)

        query = query.order_by(AuditLog.timestamp.desc())
        result = await self._db.execute(query)
        return list(result.scalars().all())
