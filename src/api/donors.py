"""Donors router.

Endpoints:
  POST /donors         — create donor profile (public)
  GET  /donors         — paginated list with search/filter (staff only)
  GET  /donors/export  — CSV export (staff only)
  GET  /donors/{id}    — get donor profile (staff only)
"""

import csv
import io
from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.donation import Donation, DonationStatus, Donor
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.donation import DonorCreate, DonorListResponse, DonorResponse
from src.schemas.error import RESOURCE_RESPONSES

router = APIRouter(prefix="/donors", tags=["donors"], responses=RESOURCE_RESPONSES)

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100

_DONOR_CSV_HEADERS = [
    "id",
    "full_name",
    "email",
    "country",
    "currency_preference",
    "gdpr_consent_at",
    "total_donations",
    "total_donated_cents",
    "created_at",
    "updated_at",
]

_ALLOWED_SORT_FIELDS = {"full_name", "email", "created_at"}


def _build_donor_list_query(
    search: str | None,
    country: str | None,
    has_gdpr_consent: bool | None,
    sort_by: str,
    sort_order: str,
) -> Select:
    """Build a SELECT statement for the donors list with optional filters."""
    stmt = select(Donor)

    if search is not None:
        pattern = f"%{search}%"
        stmt = stmt.where(Donor.full_name.ilike(pattern) | Donor.email.ilike(pattern))

    if country is not None:
        stmt = stmt.where(Donor.country == country.upper())

    if has_gdpr_consent is True:
        stmt = stmt.where(Donor.gdpr_consent_at.is_not(None))
    elif has_gdpr_consent is False:
        stmt = stmt.where(Donor.gdpr_consent_at.is_(None))

    sort_column = getattr(Donor, sort_by)
    if sort_order == "asc":
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())

    return stmt


@router.post("", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
async def create_donor(
    payload: DonorCreate,
    db: AsyncSession = Depends(get_db),
) -> Donor:
    donor = Donor(
        full_name=payload.full_name,
        email=str(payload.email),
        country=payload.country,
        currency_preference=payload.currency_preference.value,
        gdpr_consent_at=payload.gdpr_consent_at,
    )
    db.add(donor)
    try:
        await db.flush()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A donor with this email already exists",
        ) from exc
    await db.refresh(donor)
    return donor


@router.get("/export")
async def export_donors_csv(
    search: str | None = Query(default=None, min_length=1, max_length=255),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    has_gdpr_consent: bool | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> StreamingResponse:
    """Export all donors matching filters as a CSV file (staff only)."""
    if sort_by not in _ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"sort_by must be one of: {', '.join(sorted(_ALLOWED_SORT_FIELDS))}",
        )

    stmt = _build_donor_list_query(search, country, has_gdpr_consent, sort_by, sort_order)
    result = await db.execute(stmt)
    donors = list(result.scalars().all())

    # Fetch donation stats per donor in a single query
    donor_ids = [d.id for d in donors]
    donation_stats: dict[UUID, tuple[int, int]] = {}
    if donor_ids:
        stats_stmt = (
            select(
                Donation.donor_id,
                func.count(Donation.id).label("total_count"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Donation.status == DonationStatus.COMPLETED.value,
                                Donation.amount_cents,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("total_cents"),
            )
            .where(Donation.donor_id.in_(donor_ids))
            .group_by(Donation.donor_id)
        )
        stats_result = await db.execute(stats_stmt)
        for row in stats_result:
            donation_stats[row.donor_id] = (row.total_count, row.total_cents)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_DONOR_CSV_HEADERS)
    for donor in donors:
        total_count, total_cents = donation_stats.get(donor.id, (0, 0))
        writer.writerow(
            [
                str(donor.id),
                donor.full_name,
                donor.email,
                donor.country or "",
                donor.currency_preference,
                donor.gdpr_consent_at.isoformat() if donor.gdpr_consent_at else "",
                str(total_count),
                str(total_cents),
                donor.created_at.isoformat(),
                donor.updated_at.isoformat(),
            ]
        )

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=donors-export.csv"},
    )


@router.get("", response_model=list[DonorListResponse])
async def list_donors(
    search: str | None = Query(default=None, min_length=1, max_length=255),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    has_gdpr_consent: bool | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[dict]:
    """Paginated, searchable donor list (staff only).

    Includes donation summary stats (count and total completed amount) per donor.
    """
    if sort_by not in _ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"sort_by must be one of: {', '.join(sorted(_ALLOWED_SORT_FIELDS))}",
        )

    stmt = _build_donor_list_query(search, country, has_gdpr_consent, sort_by, sort_order)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    donors = list(result.scalars().all())

    # Fetch donation stats per donor in a single query
    donor_ids = [d.id for d in donors]
    donation_stats: dict[UUID, tuple[int, int]] = {}
    if donor_ids:
        stats_stmt = (
            select(
                Donation.donor_id,
                func.count(Donation.id).label("total_count"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Donation.status == DonationStatus.COMPLETED.value,
                                Donation.amount_cents,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("total_cents"),
            )
            .where(Donation.donor_id.in_(donor_ids))
            .group_by(Donation.donor_id)
        )
        stats_result = await db.execute(stats_stmt)
        for row in stats_result:
            donation_stats[row.donor_id] = (row.total_count, row.total_cents)

    # Build response with embedded stats
    response = []
    for donor in donors:
        total_count, total_cents = donation_stats.get(donor.id, (0, 0))
        donor_dict = {
            "id": donor.id,
            "full_name": donor.full_name,
            "email": donor.email,
            "country": donor.country,
            "currency_preference": donor.currency_preference,
            "gdpr_consent_at": donor.gdpr_consent_at,
            "created_at": donor.created_at,
            "updated_at": donor.updated_at,
            "total_donations": total_count,
            "total_donated_cents": total_cents,
        }
        response.append(donor_dict)

    return response



@router.get("/{donor_id}/annual-summary/{year}")
async def get_donor_annual_summary(
    donor_id: UUID,
    year: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> StreamingResponse:
    """Generate an annual donation summary PDF for a donor (staff only).

    Returns a PDF listing all completed donations in the given calendar year,
    with totals per currency and EU/Dutch tax deductibility guidance.
    """
    from datetime import datetime

    from sqlalchemy import extract

    from src.db.models.donation import DonationStatus
    from src.services.annual_donation_summary_service import (
        AnnualDonationSummaryGenerator,
        AnnualSummaryData,
        DonationLineItem,
    )

    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")

    # Fetch all completed donations for this donor in the given year
    stmt = (
        select(Donation)
        .where(Donation.donor_id == donor_id)
        .where(Donation.status == DonationStatus.COMPLETED.value)
        .where(extract("year", Donation.created_at) == year)
        .order_by(Donation.created_at.asc())
    )
    result = await db.execute(stmt)
    db_donations = list(result.scalars().all())

    line_items = [
        DonationLineItem(
            donation_id=d.id,
            date=d.created_at,
            amount_cents=d.amount_cents,
            currency=d.currency,
            payment_method=d.payment_method,
            fund_category=d.fund_category,
            receipt_number=d.receipt_number,
        )
        for d in db_donations
    ]

    # Compute totals per currency
    totals: dict[str, int] = {}
    for item in line_items:
        totals[item.currency] = totals.get(item.currency, 0) + item.amount_cents

    summary_data = AnnualSummaryData(
        donor_id=donor.id,
        donor_name=donor.full_name,
        donor_email=donor.email,
        donor_country=donor.country,
        year=year,
        donations=line_items,
        totals_by_currency=totals,
        generated_at=datetime.now(UTC),
    )

    generator = AnnualDonationSummaryGenerator()
    pdf_bytes = generator.generate_bytes(summary_data)

    filename = f"annual-summary-{year}-{str(donor_id)[:8]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/{donor_id}", response_model=DonorResponse)
async def get_donor(
    donor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Donor:
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")
    return donor
