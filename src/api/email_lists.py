"""Email list management endpoints (staff/admin only).

Endpoints:
  POST   /email-lists                        — create a new email list
  GET    /email-lists                        — list all email lists
  GET    /email-lists/{id}                   — get list detail with subscriber count
  PATCH  /email-lists/{id}                   — update list metadata
  DELETE /email-lists/{id}                   — archive a list

  POST   /email-lists/{id}/members           — add a subscriber
  GET    /email-lists/{id}/members           — list members
  PATCH  /email-lists/{id}/members/{mid}     — update member status
  DELETE /email-lists/{id}/members/{mid}     — remove a member

  POST   /email-lists/{id}/segment           — auto-populate from entity type
  GET    /email-lists/unsubscribe/{token}    — GDPR opt-out via token
"""

from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.email_list import EmailList, EmailListMember, EmailListStatus, MemberStatus
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.email_list import (
    EmailListCreate,
    EmailListResponse,
    EmailListSummary,
    EmailListUpdate,
    MemberAdd,
    MemberResponse,
    MemberUpdate,
    SegmentRequest,
    SegmentResult,
)
from src.schemas.error import RESOURCE_RESPONSES
from src.services import email_list_service

router = APIRouter(
    prefix="/email-lists",
    tags=["email-lists"],
    responses=RESOURCE_RESPONSES,
)


# ---------------------------------------------------------------------------
# List management
# ---------------------------------------------------------------------------


@router.post("", response_model=EmailListResponse, status_code=status.HTTP_201_CREATED)
async def create_email_list(
    payload: EmailListCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> EmailList:
    """Create a new email subscriber list. Staff or admin only."""
    email_list = EmailList(
        name=payload.name,
        description=payload.description,
        list_type=payload.list_type.value,
        status=EmailListStatus.ACTIVE.value,
        created_by_id=current_user.id,
    )
    db.add(email_list)
    await db.flush()
    await db.refresh(email_list)
    return email_list


@router.get("", response_model=list[EmailListSummary])
async def list_email_lists(
    status_filter: str | None = Query(default=None, alias="status"),
    list_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list[EmailList]:
    """List all email lists. Optionally filter by status or list_type."""
    stmt = select(EmailList)
    if status_filter:
        stmt = stmt.where(EmailList.status == status_filter)
    if list_type:
        stmt = stmt.where(EmailList.list_type == list_type)
    stmt = stmt.order_by(EmailList.created_at.desc())

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{list_id}", response_model=EmailListResponse)
async def get_email_list(
    list_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailList:
    """Get email list detail with subscriber count."""
    email_list = await db.get(EmailList, list_id)
    if email_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email list not found",
        )
    return email_list


@router.patch("/{list_id}", response_model=EmailListResponse)
async def update_email_list(
    list_id: UUID,
    payload: EmailListUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailList:
    """Update email list metadata. Staff or admin only."""
    email_list = await db.get(EmailList, list_id)
    if email_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email list not found",
        )
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(email_list, field, value)

    await db.flush()
    await db.refresh(email_list)
    return email_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_email_list(
    list_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> None:
    """Archive an email list (soft delete). Staff or admin only."""
    email_list = await db.get(EmailList, list_id)
    if email_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email list not found",
        )
    email_list.status = EmailListStatus.ARCHIVED.value
    await db.flush()


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


@router.post(
    "/{list_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    list_id: UUID,
    payload: MemberAdd,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailListMember:
    """Add a subscriber to an email list."""
    email_list = await db.get(EmailList, list_id)
    if email_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email list not found",
        )

    normalized_email = str(payload.email).lower()

    # Check for duplicate
    existing = await db.execute(
        select(EmailListMember).where(
            EmailListMember.email_list_id == list_id,
            EmailListMember.email == normalized_email,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already a member of this list",
        )

    member = EmailListMember(
        email_list_id=list_id,
        email=normalized_email,
        name=payload.name,
        status=MemberStatus.SUBSCRIBED.value,
        source_type=payload.source_type or "manual",
        source_id=payload.source_id,
    )
    db.add(member)
    await db.flush()
    await db.refresh(member)
    return member


@router.get("/{list_id}/members", response_model=list[MemberResponse])
async def list_members(
    list_id: UUID,
    member_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list[EmailListMember]:
    """List members of an email list with optional status filter."""
    email_list = await db.get(EmailList, list_id)
    if email_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email list not found",
        )

    stmt = select(EmailListMember).where(EmailListMember.email_list_id == list_id)
    if member_status:
        stmt = stmt.where(EmailListMember.status == member_status)
    stmt = stmt.order_by(EmailListMember.subscribed_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.patch("/{list_id}/members/{member_id}", response_model=MemberResponse)
async def update_member(
    list_id: UUID,
    member_id: UUID,
    payload: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> EmailListMember:
    """Update a member's subscription status."""
    result = await db.execute(
        select(EmailListMember).where(
            EmailListMember.id == member_id,
            EmailListMember.email_list_id == list_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    member.status = payload.status.value
    if payload.status == MemberStatus.UNSUBSCRIBED and member.unsubscribed_at is None:
        from datetime import datetime

        member.unsubscribed_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(member)
    return member


@router.delete("/{list_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    list_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> None:
    """Remove a subscriber from a list."""
    result = await db.execute(
        select(EmailListMember).where(
            EmailListMember.id == member_id,
            EmailListMember.email_list_id == list_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )
    await db.delete(member)
    await db.flush()


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------


@router.post("/{list_id}/segment", response_model=SegmentResult)
async def populate_segment(
    list_id: UUID,
    payload: SegmentRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SegmentResult:
    """Auto-populate an email list from an entity segment (donors, adopters, etc.)."""
    email_list = await db.get(EmailList, list_id)
    if email_list is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email list not found",
        )

    # Temporarily update list type to match the requested segment
    email_list.list_type = payload.list_type.value

    counts = await email_list_service.populate_from_segment(
        db, email_list, overwrite=payload.overwrite
    )
    return SegmentResult(**counts)


# ---------------------------------------------------------------------------
# Unsubscribe (public — no auth required)
# ---------------------------------------------------------------------------


@router.get("/unsubscribe/{token}", tags=["public"])
async def unsubscribe(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """GDPR-compliant opt-out via unsubscribe token (no authentication required)."""
    member = await email_list_service.unsubscribe_by_token(db, token)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired unsubscribe token",
        )
    return {"message": "You have been successfully unsubscribed", "email": member.email}
