"""Audit trail service: write and query audit log entries.

Provides:
- create_audit_entry: Persist an audit log record to the database
- query_audit_logs: Filtered, paginated query for audit log entries
- audit_event_handler: Event bus handler that persists audit events
"""

import logging
import math
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.audit_log import AuditLog
from src.events.base import DomainEvent
from src.schemas.audit_log import AuditLogFilter, AuditLogListResponse, AuditLogResponse

logger = logging.getLogger(__name__)


async def create_audit_entry(db: AsyncSession, **kwargs: object) -> AuditLog:
    """Create and persist a single audit log entry.

    Args:
        db: Active database session.
        **kwargs: Fields matching AuditLog column names.

    Returns:
        The created AuditLog instance.
    """
    entry = AuditLog(**kwargs)
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def query_audit_logs(
    db: AsyncSession,
    filters: AuditLogFilter,
) -> AuditLogListResponse:
    """Query audit logs with filtering and pagination.

    Args:
        db: Active database session.
        filters: Filter criteria and pagination parameters.

    Returns:
        Paginated response with matching audit log entries.
    """
    # Base query
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    # Apply filters
    if filters.user_id is not None:
        query = query.where(AuditLog.user_id == filters.user_id)
        count_query = count_query.where(AuditLog.user_id == filters.user_id)

    if filters.action is not None:
        query = query.where(AuditLog.action == filters.action)
        count_query = count_query.where(AuditLog.action == filters.action)

    if filters.resource_type is not None:
        query = query.where(AuditLog.resource_type == filters.resource_type)
        count_query = count_query.where(AuditLog.resource_type == filters.resource_type)

    if filters.resource_id is not None:
        query = query.where(AuditLog.resource_id == filters.resource_id)
        count_query = count_query.where(AuditLog.resource_id == filters.resource_id)

    if filters.date_from is not None:
        query = query.where(AuditLog.timestamp >= filters.date_from)
        count_query = count_query.where(AuditLog.timestamp >= filters.date_from)

    if filters.date_to is not None:
        query = query.where(AuditLog.timestamp <= filters.date_to)
        count_query = count_query.where(AuditLog.timestamp <= filters.date_to)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering and pagination
    offset = (filters.page - 1) * filters.page_size
    query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(filters.page_size)

    result = await db.execute(query)
    entries = list(result.scalars().all())

    pages = max(1, math.ceil(total / filters.page_size))

    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(e) for e in entries],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=pages,
    )


async def audit_event_handler(event: DomainEvent) -> None:
    """Event bus handler that persists audit events to the database.

    This handler is registered with the event bus during app startup.
    It receives audit events published by the AuditMiddleware and writes
    them to the audit_logs table.

    Note: This handler creates its own database session because event bus
    handlers run outside the request lifecycle.
    """
    from src.db.session import get_session_factory

    payload = event.payload
    session_factory = get_session_factory()

    if session_factory is None:
        logger.error("Cannot persist audit event — no database session factory available")
        return

    async with session_factory() as session:
        entry = AuditLog(
            user_id=UUID(payload["user_id"]),
            action=payload["action"],
            resource_type=payload["resource_type"],
            resource_id=payload.get("resource_id"),
            ip_address=payload.get("ip_address"),
            user_agent=payload.get("user_agent"),
            http_method=payload["http_method"],
            path=payload["path"],
            status_code=payload["status_code"],
        )
        session.add(entry)
        await session.commit()
        logger.debug(
            "Audit entry persisted: %s %s %s by user %s",
            payload["action"],
            payload["resource_type"],
            payload.get("resource_id", "N/A"),
            payload["user_id"],
        )
