"""In-Kind Donations router.

Endpoints:
  POST   /in-kind-donations              -- record an in-kind donation (staff only)
  GET    /in-kind-donations              -- paginated list with filters (staff only)
  GET    /in-kind-donations/{id}         -- single in-kind donation (staff only)
  PUT    /in-kind-donations/{id}         -- update in-kind donation (staff only)
  DELETE /in-kind-donations/{id}         -- delete in-kind donation (staff only)
  GET    /donors/{id}/giving-summary     -- combined cash + in-kind totals (staff only)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.donation import (
    CurrencyCode,
    Donation,
    DonationStatus,
    Donor,
    InKindDonation,
    ItemType,
)
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.in_kind_donation import (
    DonorGivingSummary,
    InKindDonationCreate,
    InKindDonationListResponse,
    InKindDonationResponse,
    InKindDonationUpdate,
)

router = APIRouter(tags=["in-kind-donations"])


@router.post(
    "/in-kind-donations",
    response_model=InKindDonationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_in_kind_donation(
    payload: InKindDonationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> InKindDonation:
    """Record a new in-kind donation. Staff only."""
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
        received_by_staff_id=current_user.id,
        notes=payload.notes,
    )
    if payload.date_received is not None:
        donation.date_received = payload.date_received

    db.add(donation)
    await db.flush()
    await db.refresh(donation)
    return donation


@router.get("/in-kind-donations", response_model=InKindDonationListResponse)
async def list_in_kind_donations(
    item_type: str | None = Query(default=None),
    donor_id: UUID | None = Query(default=None),
    currency: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> InKindDonationListResponse:
    """List in-kind donations with optional filters. Staff only."""
    base_stmt = select(InKindDonation)
    count_stmt = select(func.count(InKindDonation.id))

    if item_type is not None:
        base_stmt = base_stmt.where(InKindDonation.item_type == item_type.lower())
        count_stmt = count_stmt.where(InKindDonation.item_type == item_type.lower())
    if donor_id is not None:
        base_stmt = base_stmt.where(InKindDonation.donor_id == donor_id)
        count_stmt = count_stmt.where(InKindDonation.donor_id == donor_id)
    if currency is not None:
        base_stmt = base_stmt.where(InKindDonation.currency == currency.upper())
        count_stmt = count_stmt.where(InKindDonation.currency == currency.upper())

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    query = base_stmt.order_by(InKindDonation.date_received.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return InKindDonationListResponse(
        items=items,  # type: ignore[arg-type]
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/in-kind-donations/{donation_id}", response_model=InKindDonationResponse)
async def get_in_kind_donation(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> InKindDonation:
    """Get a single in-kind donation. Staff only."""
    donation = await db.get(InKindDonation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="In-kind donation not found",
        )
    return donation


@router.put("/in-kind-donations/{donation_id}", response_model=InKindDonationResponse)
async def update_in_kind_donation(
    donation_id: UUID,
    payload: InKindDonationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> InKindDonation:
    """Update an in-kind donation. Staff only."""
    donation = await db.get(InKindDonation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="In-kind donation not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            # Convert enum values to their string representation
            if isinstance(value, (ItemType, CurrencyCode)):
                value = value.value
            setattr(donation, field, value)

    await db.flush()
    await db.refresh(donation)
    return donation


@router.delete(
    "/in-kind-donations/{donation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_in_kind_donation(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    """Delete an in-kind donation. Staff only."""
    donation = await db.get(InKindDonation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="In-kind donation not found",
        )
    await db.delete(donation)
    await db.flush()


@router.get(
    "/donors/{donor_id}/giving-summary",
    response_model=DonorGivingSummary,
)
async def get_donor_giving_summary(
    donor_id: UUID,
    currency: str = Query(default="EUR"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> DonorGivingSummary:
    """Get combined cash + in-kind giving summary for a donor. Staff only."""
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    currency_upper = currency.upper()

    # Cash donations total (only completed)
    cash_stmt = select(
        func.coalesce(func.sum(Donation.amount_cents), 0).label("total"),
        func.count(Donation.id).label("count"),
    ).where(
        Donation.donor_id == donor_id,
        Donation.currency == currency_upper,
        Donation.status == DonationStatus.COMPLETED.value,
    )
    cash_result = await db.execute(cash_stmt)
    cash_row = cash_result.one()

    # In-kind donations total
    inkind_stmt = select(
        func.coalesce(func.sum(InKindDonation.estimated_value_cents), 0).label("total"),
        func.count(InKindDonation.id).label("count"),
    ).where(
        InKindDonation.donor_id == donor_id,
        InKindDonation.currency == currency_upper,
    )
    inkind_result = await db.execute(inkind_stmt)
    inkind_row = inkind_result.one()

    cash_total: int = cash_row.total  # type: ignore[assignment]
    cash_count: int = cash_row.count  # type: ignore[assignment]
    inkind_total: int = inkind_row.total  # type: ignore[assignment]
    inkind_count: int = inkind_row.count  # type: ignore[assignment]

    return DonorGivingSummary(
        donor_id=donor_id,
        donor_name=donor.full_name,
        cash_total_cents=cash_total,
        cash_donation_count=cash_count,
        in_kind_total_cents=inkind_total,
        in_kind_donation_count=inkind_count,
        combined_total_cents=cash_total + inkind_total,
        currency=currency_upper,
    )
