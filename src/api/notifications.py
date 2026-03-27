"""In-app notifications router.

Endpoints for listing, reading, and managing notifications for the
current authenticated user. All endpoints require staff role minimum.

Endpoints:
    GET    /notifications              -- list notifications (paginated, filterable)
    GET    /notifications/unread-count -- get count of unread notifications
    POST   /notifications              -- create notification (admin only)
    PATCH  /notifications/{id}/read    -- mark single notification as read
    POST   /notifications/mark-all-read -- mark all as read
    DELETE /notifications/{id}         -- delete a notification
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin, require_staff
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.notification import (
    MarkAllReadResponse,
    NotificationCreateRequest,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from src.services.notification_service import (
    create_notification,
    delete_notification,
    get_unread_count,
    list_notifications,
    mark_all_read,
    mark_read,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"], responses=RESOURCE_RESPONSES)


@router.get("", response_model=NotificationListResponse)
async def list_user_notifications(
    is_read: bool | None = Query(None, description="Filter by read status"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> NotificationListResponse:
    """List notifications for the current user with optional filters."""
    items = await list_notifications(
        db,
        current_user.id,
        is_read=is_read,
        offset=offset,
        limit=limit,
    )
    # Get total unread for context
    unread = await get_unread_count(db, current_user.id)
    total = unread if is_read is False else len(items)

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_user_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> UnreadCountResponse:
    """Get the count of unread notifications for the current user."""
    count = await get_unread_count(db, current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_user_notification(
    payload: NotificationCreateRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> NotificationResponse:
    """Create a notification for a specific user (admin only)."""
    notification = await create_notification(
        db,
        user_id=payload.user_id,
        notification_type=payload.notification_type,
        title=payload.title,
        message=payload.message,
        data=payload.data,
    )
    return NotificationResponse.model_validate(notification)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> NotificationResponse:
    """Mark a single notification as read."""
    notification = await mark_read(db, notification_id, current_user.id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read", response_model=MarkAllReadResponse)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> MarkAllReadResponse:
    """Mark all unread notifications as read for the current user."""
    count = await mark_all_read(db, current_user.id)
    return MarkAllReadResponse(marked_count=count)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> None:
    """Delete a notification."""
    deleted = await delete_notification(db, notification_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
