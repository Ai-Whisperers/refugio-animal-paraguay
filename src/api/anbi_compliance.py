"""ANBI compliance documentation endpoints (RAP-167).

Provides endpoints for generating Dutch ANBI compliance documents:
  GET /donors/{id}/anbi-letter/{year}  -- per-donor ANBI gift confirmation letter
  GET /admin/anbi-declaration/{year}   -- annual ANBI compliance declaration (internal)
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.donation import Donation, DonationStatus, Donor
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import RESOURCE_RESPONSES

router = APIRouter(tags=["anbi-compliance"], responses=RESOURCE_RESPONSES)


@router.get("/donors/{donor_id}/anbi-letter/{year}")
async def get_donor_anbi_letter(
    donor_id: UUID,
    year: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> StreamingResponse:
    """Generate an ANBI gift confirmation letter for a donor (staff only).

    Useful for EU/Dutch donors claiming tax deductions on their donations.
    """
    from sqlalchemy import select

    from src.services.anbi_compliance_service import ANBIComplianceService, ANBILetterData

    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")

    # Sum completed donations for the year
    stmt = (
        select(
            func.coalesce(func.sum(Donation.amount_cents), 0).label("total"),
            Donation.currency,
        )
        .where(Donation.donor_id == donor_id)
        .where(Donation.status == DonationStatus.COMPLETED.value)
        .where(extract("year", Donation.created_at) == year)
        .group_by(Donation.currency)
        .order_by(func.coalesce(func.sum(Donation.amount_cents), 0).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    total_cents = sum(row.total for row in rows)
    primary_currency = rows[0].currency if rows else donor.currency_preference

    letter_data = ANBILetterData(
        donor_id=donor.id,
        donor_name=donor.full_name,
        donor_email=donor.email,
        donor_country=donor.country,
        year=year,
        total_donated_cents=total_cents,
        primary_currency=primary_currency,
        generated_at=datetime.now(UTC),
    )

    service = ANBIComplianceService()
    pdf_bytes = service.generate_donor_letter_bytes(letter_data)

    filename = f"anbi-letter-{year}-{str(donor_id)[:8]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/admin/anbi-declaration/{year}")
async def get_annual_anbi_declaration(
    year: int,
    generated_by: str = Query(default="Administrator", max_length=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> StreamingResponse:
    """Generate the annual ANBI compliance declaration (staff only, internal document)."""
    from sqlalchemy import case, select

    from src.services.anbi_compliance_service import ANBIComplianceService, ANBIDeclarationData

    base_filter = [
        Donation.status == DonationStatus.COMPLETED.value,
        extract("year", Donation.created_at) == year,
    ]

    # Aggregate totals
    stmt = select(
        func.count(func.distinct(Donation.donor_id)).label("total_donors"),
        func.coalesce(func.sum(Donation.amount_cents), 0).label("total_cents"),
        func.coalesce(
            func.sum(case((Donation.currency == "EUR", Donation.amount_cents), else_=0)), 0
        ).label("eur_cents"),
        func.coalesce(
            func.sum(case((Donation.currency == "PYG", Donation.amount_cents), else_=0)), 0
        ).label("pyg_cents"),
    ).where(*base_filter)

    agg_result = await db.execute(stmt)
    agg = agg_result.one()

    # EU donors (country in EU countries)
    eu_countries = ["NL", "DE", "BE", "FR", "ES", "IT", "AT", "SE", "DK", "FI", "PT", "IE"]
    eu_stmt = (
        select(func.count(func.distinct(Donation.donor_id)))
        .join(Donor, Donation.donor_id == Donor.id)
        .where(*base_filter)
        .where(Donor.country.in_(eu_countries))
    )
    eu_result = await db.execute(eu_stmt)
    eu_donors = eu_result.scalar() or 0

    # Top fund categories
    fund_stmt = (
        select(
            Donation.fund_category,
            func.sum(Donation.amount_cents).label("total"),
        )
        .where(*base_filter)
        .where(Donation.fund_category.is_not(None))
        .group_by(Donation.fund_category)
        .order_by(func.sum(Donation.amount_cents).desc())
        .limit(5)
    )
    fund_result = await db.execute(fund_stmt)
    top_funds = [(row.fund_category or "unknown", row.total) for row in fund_result.all()]

    declaration_data = ANBIDeclarationData(
        year=year,
        total_donors=agg.total_donors or 0,
        total_eu_donors=eu_donors,
        total_donations_cents=agg.total_cents or 0,
        total_eur_cents=agg.eur_cents or 0,
        total_pyg_cents=agg.pyg_cents or 0,
        top_fund_categories=top_funds,
        generated_at=datetime.now(UTC),
        generated_by=generated_by,
    )

    service = ANBIComplianceService()
    pdf_bytes = service.generate_declaration_bytes(declaration_data)

    filename = f"anbi-declaration-{year}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
