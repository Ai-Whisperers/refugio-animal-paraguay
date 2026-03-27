"""In-kind donations router.

Endpoints:
  POST /in-kind-donations          -- record in-kind donation (staff only)
  GET  /in-kind-donations          -- paginated list with filters (staff only)
  GET  /in-kind-donations/{id}     -- single in-kind donation (staff only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.donation import Donor
from src.db.models.in_kind_donation import InKindDonation
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES
from src.schemas.in_kind_donation import (
    InKindDonationCreate,
    InKindDonationListResponse,
    InKindDonationResponse,
)

router = APIRouter(
    prefix="/in-kind-donations", tags=["in-kind-donations"], responses=RESOURCE_RESPONSES
)


@router.post("", response_model=InKindDonationResponse, status_code=status.HTTP_201_CREATED)
async def record_in_kind_donation(
    payload: InKindDonationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> InKindDonation:
    """Record a non-cash donation received at the shelter. Staff only."""
    if payload.donor_id is not None:
        donor = await db.get(Donor, payload.donor_id)
        if donor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor not found",
            )

    donation = InKindDonation(
        donor_id=payload.donor_id,
        item_type=payload.item_type.value,
        description=payload.description,
        quantity=payload.quantity,
        estimated_value_cents=payload.estimated_value_cents,
        currency=payload.currency.value,
        received_by_user_id=current_user.id,
        notes=payload.notes,
    )
    if payload.date_received is not None:
        donation.date_received = payload.date_received

    db.add(donation)
    await db.flush()
    await db.refresh(donation)
    return donation


@router.get("", response_model=InKindDonationListResponse)
async def list_in_kind_donations(
    item_type: str | None = Query(default=None, description="Filter by item type"),
    donor_id: UUID | None = Query(default=None, description="Filter by donor ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> InKindDonationListResponse:
    """List in-kind donations with optional filters. Staff only."""
    base_query = select(InKindDonation)
    count_query = select(func.count()).select_from(InKindDonation)

    if item_type is not None:
        base_query = base_query.where(InKindDonation.item_type == item_type)
        count_query = count_query.where(InKindDonation.item_type == item_type)
    if donor_id is not None:
        base_query = base_query.where(InKindDonation.donor_id == donor_id)
        count_query = count_query.where(InKindDonation.donor_id == donor_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    stmt = base_query.order_by(InKindDonation.date_received.desc()).limit(page_size).offset(offset)
    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return InKindDonationListResponse(
        items=[InKindDonationResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{donation_id}", response_model=InKindDonationResponse)
async def get_in_kind_donation(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> InKindDonation:
    """Get a single in-kind donation by ID. Staff only."""
    donation = await db.get(InKindDonation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="In-kind donation not found",
        )
    return donation
