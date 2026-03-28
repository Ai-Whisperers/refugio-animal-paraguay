"""Donations router.

Endpoints:
  POST /donations                    — create donation record (public; anonymous if no donor_id)
  POST /donations/cash               — record cash donation (staff only, immediate completion)
  POST /donations/{id}/stripe-intent — create Stripe PaymentIntent, return client_secret (public)
  GET  /donations/stats              — aggregated dashboard stats (staff only)
  GET  /donations/export             — CSV export of donation history (staff only)
  GET  /donations                    — paginated list with filters (staff only)
  GET  /donations/{id}               — single donation (staff only)
  GET  /donations/{id}/receipt       — PDF receipt for a single donation (staff only)
"""

import csv
import io
import os
from datetime import datetime
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.campaign import Campaign, CampaignDonation, CampaignStatus
from src.db.models.donation import Donation, DonationStatus, Donor
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.donation import (
    CashDonationCreate,
    CurrencyBreakdown,
    DonationCreate,
    DonationResponse,
    DonationStatsResponse,
    PaymentMethodBreakdown,
    StatusBreakdown,
    StripeIntentResponse,
)
from src.schemas.error import PAYMENT_RESPONSES
from src.services.donation_target_service import (
    InvalidTargetError,
    TargetNotActiveError,
    validate_donation_target,
)

router = APIRouter(prefix="/donations", tags=["donations"], responses=PAYMENT_RESPONSES)

_STRIPE_CURRENCY_MAP = {
    "EUR": "eur",
    "USD": "usd",
    # PYG is not supported by Stripe — only cash/transfer for local PYG donations
}

_CSV_HEADERS = [
    "id",
    "donor_id",
    "amount_cents",
    "currency",
    "payment_method",
    "status",
    "fund_category",
    "target_type",
    "target_id",
    "is_recurring",
    "recurring_interval",
    "receipt_number",
    "stripe_payment_intent_id",
    "stripe_subscription_id",
    "notes",
    "created_at",
    "updated_at",
]


def _get_stripe_key() -> str:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )
    return key


def _apply_common_filters(
    stmt: object,
    currency: str | None,
    donation_status: str | None,
    donor_id: UUID | None,
    fund_category: str | None,
    payment_method: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    target_type: str | None = None,
    target_id: UUID | None = None,
) -> object:
    """Apply the shared set of donation filter predicates to a select statement."""
    if currency is not None:
        stmt = stmt.where(Donation.currency == currency.upper())  # type: ignore[union-attr]
    if donation_status is not None:
        stmt = stmt.where(Donation.status == donation_status.lower())  # type: ignore[union-attr]
    if donor_id is not None:
        stmt = stmt.where(Donation.donor_id == donor_id)  # type: ignore[union-attr]
    if fund_category is not None:
        stmt = stmt.where(Donation.fund_category == fund_category.lower())  # type: ignore[union-attr]
    if payment_method is not None:
        stmt = stmt.where(Donation.payment_method == payment_method.lower())  # type: ignore[union-attr]
    if date_from is not None:
        stmt = stmt.where(Donation.created_at >= date_from)  # type: ignore[union-attr]
    if date_to is not None:
        stmt = stmt.where(Donation.created_at <= date_to)  # type: ignore[union-attr]
    if target_type is not None:
        stmt = stmt.where(Donation.target_type == target_type)  # type: ignore[union-attr]
    if target_id is not None:
        stmt = stmt.where(Donation.target_id == target_id)  # type: ignore[union-attr]
    return stmt


def _donation_to_csv_row(d: Donation) -> list[str]:
    """Convert a Donation ORM object to a CSV-serialisable list of strings."""
    return [
        str(d.id),
        str(d.donor_id) if d.donor_id else "",
        str(d.amount_cents),
        d.currency,
        d.payment_method,
        d.status,
        d.fund_category or "",
        d.target_type or "general",
        str(d.target_id) if d.target_id else "",
        str(d.is_recurring),
        d.recurring_interval or "",
        d.receipt_number or "",
        d.stripe_payment_intent_id or "",
        d.stripe_subscription_id or "",
        d.notes or "",
        d.created_at.isoformat(),
        d.updated_at.isoformat(),
    ]


@router.post("", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def create_donation(
    payload: DonationCreate,
    db: AsyncSession = Depends(get_db),
) -> Donation:
    # Verify donor exists if a donor_id was supplied
    if payload.donor_id is not None:
        donor = await db.get(Donor, payload.donor_id)
        if donor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor not found",
            )

    # Verify campaign exists and is active if a campaign_id was supplied
    if payload.campaign_id is not None:
        campaign = await db.get(Campaign, payload.campaign_id)
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )
        if campaign.status != CampaignStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Campaign is not accepting donations",
            )
        # Validate donation amount against campaign limits
        if campaign.min_donation_cents and payload.amount_cents < campaign.min_donation_cents:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Minimum donation for this campaign is {campaign.min_donation_cents} cents",
            )
        if campaign.max_donation_cents and payload.amount_cents > campaign.max_donation_cents:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Maximum donation for this campaign is {campaign.max_donation_cents} cents",
            )

    # Validate donation target if specified
    try:
        await validate_donation_target(db, payload.target_type.value, payload.target_id)
    except InvalidTargetError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        ) from None
    except TargetNotActiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        ) from None

    donation = Donation(
        donor_id=payload.donor_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency.value,
        payment_method=payload.payment_method.value,
        target_type=payload.target_type.value,
        target_id=payload.target_id,
        notes=payload.notes,
    )
    db.add(donation)
    await db.flush()
    await db.refresh(donation)

    # Link donation to campaign if specified
    if payload.campaign_id is not None:
        campaign_donation = CampaignDonation(
            campaign_id=payload.campaign_id,
            donation_id=donation.id,
        )
        db.add(campaign_donation)
        await db.flush()

    return donation


@router.post("/cash", response_model=DonationResponse, status_code=status.HTTP_201_CREATED)
async def record_cash_donation(
    payload: CashDonationCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> Donation:
    """Record a cash donation received at the shelter. Staff only.

    Cash donations are created with status=completed immediately
    since the money has already been received.
    """
    if payload.donor_id is not None:
        donor = await db.get(Donor, payload.donor_id)
        if donor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor not found",
            )

    donation = Donation(
        donor_id=payload.donor_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency.value,
        payment_method="cash",
        status="completed",
        receipt_number=payload.receipt_number,
        notes=payload.notes,
    )
    db.add(donation)
    await db.flush()
    await db.refresh(donation)
    return donation


@router.post(
    "/{donation_id}/stripe-intent",
    response_model=StripeIntentResponse,
)
async def create_stripe_intent(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> StripeIntentResponse:
    donation = await db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    if donation.status != DonationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot create payment intent for donation with status '{donation.status}'",
        )

    if donation.currency not in _STRIPE_CURRENCY_MAP:
        raise HTTPException(
            status_code=422,
            detail=f"Currency '{donation.currency}' is not supported by Stripe. Use cash or transfer for PYG.",
        )

    stripe.api_key = _get_stripe_key()
    intent = stripe.PaymentIntent.create(
        amount=donation.amount_cents,
        currency=_STRIPE_CURRENCY_MAP[donation.currency],
        metadata={"donation_id": str(donation_id)},
    )

    if intent.client_secret is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe did not return a client secret",
        )

    donation.stripe_payment_intent_id = intent.id
    await db.flush()

    return StripeIntentResponse(
        donation_id=donation_id,
        stripe_payment_intent_id=intent.id,
        client_secret=intent.client_secret,
        amount_cents=donation.amount_cents,
        currency=donation.currency,  # type: ignore[arg-type]
    )


@router.get("/stats", response_model=DonationStatsResponse)
async def get_donation_stats(
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> DonationStatsResponse:
    """Aggregated donation statistics for the staff dashboard. Staff only.

    Returns total count, breakdown by currency (with total amount), breakdown
    by status (count only), and breakdown by payment method (with total amount).
    All aggregations respect the optional date_from / date_to window.
    """
    base_filter: list = []
    if date_from is not None:
        base_filter.append(Donation.created_at >= date_from)
    if date_to is not None:
        base_filter.append(Donation.created_at <= date_to)

    # Total count
    total_stmt = select(func.count(Donation.id))
    for f in base_filter:
        total_stmt = total_stmt.where(f)
    total_result = await db.execute(total_stmt)
    total_donations: int = total_result.scalar_one() or 0

    # By currency: count + sum
    currency_stmt = (
        select(
            Donation.currency,
            func.count(Donation.id).label("donation_count"),
            func.sum(Donation.amount_cents).label("total_amount_cents"),
        )
        .group_by(Donation.currency)
        .order_by(Donation.currency)
    )
    for f in base_filter:
        currency_stmt = currency_stmt.where(f)
    currency_result = await db.execute(currency_stmt)
    by_currency = [
        CurrencyBreakdown(
            currency=row.currency,
            count=row.donation_count,
            total_amount_cents=row.total_amount_cents or 0,
        )
        for row in currency_result.all()
    ]

    # By status: count only
    status_stmt = (
        select(
            Donation.status,
            func.count(Donation.id).label("donation_count"),
        )
        .group_by(Donation.status)
        .order_by(Donation.status)
    )
    for f in base_filter:
        status_stmt = status_stmt.where(f)
    status_result = await db.execute(status_stmt)
    by_status = [
        StatusBreakdown(status=row.status, count=row.donation_count) for row in status_result.all()
    ]

    # By payment method: count + sum
    pm_stmt = (
        select(
            Donation.payment_method,
            func.count(Donation.id).label("donation_count"),
            func.sum(Donation.amount_cents).label("total_amount_cents"),
        )
        .group_by(Donation.payment_method)
        .order_by(Donation.payment_method)
    )
    for f in base_filter:
        pm_stmt = pm_stmt.where(f)
    pm_result = await db.execute(pm_stmt)
    by_payment_method = [
        PaymentMethodBreakdown(
            payment_method=row.payment_method,
            count=row.donation_count,
            total_amount_cents=row.total_amount_cents or 0,
        )
        for row in pm_result.all()
    ]

    return DonationStatsResponse(
        total_donations=total_donations,
        by_currency=by_currency,
        by_status=by_status,
        by_payment_method=by_payment_method,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/export")
async def export_donations_csv(
    currency: str | None = Query(default=None),
    donation_status: str | None = Query(default=None, alias="status"),
    donor_id: UUID | None = Query(default=None),
    fund_category: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> StreamingResponse:
    """Export donation records as a CSV file. Staff only.

    Accepts the same filter params as GET /donations. Returns a streaming
    CSV response so large datasets do not exhaust server memory.
    """
    stmt = select(Donation)
    stmt = _apply_common_filters(  # type: ignore[assignment]
        stmt,
        currency=currency,
        donation_status=donation_status,
        donor_id=donor_id,
        fund_category=fund_category,
        payment_method=payment_method,
        date_from=date_from,
        date_to=date_to,
        target_type=target_type,
        target_id=target_id,
    )
    stmt = stmt.order_by(Donation.created_at.desc())  # type: ignore[union-attr]
    result = await db.execute(stmt)
    donations = list(result.scalars().all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(_CSV_HEADERS)
    for d in donations:
        writer.writerow(_donation_to_csv_row(d))

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=donations.csv"},
    )


@router.get("", response_model=list[DonationResponse])
async def list_donations(
    currency: str | None = Query(default=None),
    donation_status: str | None = Query(default=None, alias="status"),
    donor_id: UUID | None = Query(default=None),
    fund_category: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[Donation]:
    """Paginated, filterable list of donations. Staff only."""
    stmt = select(Donation)
    stmt = _apply_common_filters(  # type: ignore[assignment]
        stmt,
        currency=currency,
        donation_status=donation_status,
        donor_id=donor_id,
        fund_category=fund_category,
        payment_method=payment_method,
        date_from=date_from,
        date_to=date_to,
        target_type=target_type,
        target_id=target_id,
    )
    stmt = stmt.order_by(Donation.created_at.desc()).limit(limit).offset(offset)  # type: ignore[union-attr]
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{donation_id}/receipt")
async def get_donation_receipt(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> StreamingResponse:
    """Generate and return a PDF receipt for a single donation. Staff only."""
    from src.services.donation_receipt_service import (
        DonationReceiptGenerator,
        ReceiptData,
    )

    donation = await db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )

    # Load donor info if available
    donor_name: str | None = None
    donor_email: str | None = None
    donor_country: str | None = None
    if donation.donor_id is not None:
        donor = await db.get(Donor, donation.donor_id)
        if donor is not None:
            donor_name = donor.full_name
            donor_email = donor.email
            donor_country = donor.country

    receipt_data = ReceiptData(
        donation_id=donation.id,
        amount_cents=donation.amount_cents,
        currency=donation.currency,
        payment_method=donation.payment_method,
        status=donation.status,
        receipt_number=donation.receipt_number,
        fund_category=donation.fund_category,
        is_recurring=donation.is_recurring,
        recurring_interval=donation.recurring_interval,
        notes=donation.notes,
        donation_date=donation.created_at,
        donor_name=donor_name,
        donor_email=donor_email,
        donor_country=donor_country,
    )

    generator = DonationReceiptGenerator()
    pdf_bytes = generator.generate_bytes(receipt_data)

    filename = f"recibo-donacion-{str(donation_id)[:8]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{donation_id}", response_model=DonationResponse)
async def get_donation(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Donation:
    donation = await db.get(Donation, donation_id)
    if donation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation not found",
        )
    return donation
