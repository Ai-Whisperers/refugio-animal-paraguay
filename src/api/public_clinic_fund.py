"""Public clinic funding API endpoints (no auth required).

Endpoints:
  GET  /public/clinics                     - List active clinics
  GET  /public/clinics/{clinic_id}         - Get clinic detail + services
  GET  /public/clinics/{clinic_id}/stats   - Get funding stats for a clinic
  POST /public/clinic-fund                 - Create a clinic-targeted donation
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.clinic_service import ClinicService
from src.db.models.donation import CurrencyCode, Donation, DonationTargetType, Donor
from src.db.models.vet_clinic import ClinicStatus, VetClinic
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["public-clinic-fund"])

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

MINIMUM_DONATION_CENTS = 500  # EUR 5.00


class PublicClinicSummary(BaseModel):
    """Clinic summary for listing."""

    id: str
    name: str
    city: str
    department: str | None = None
    specialties: str | None = None
    accepts_emergencies: bool = False

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: object) -> str:
        return str(v)


class PublicClinicListResponse(BaseModel):
    items: list[PublicClinicSummary]
    total: int
    page: int
    page_size: int


class PublicServiceSummary(BaseModel):
    """Service summary for clinic detail."""

    id: str
    name: str
    description: str | None = None
    category: str
    price_eur: float | None = None

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: object) -> str:
        return str(v)


class PublicClinicDetail(BaseModel):
    """Full clinic detail with services."""

    id: str
    name: str
    city: str
    department: str | None = None
    address: str
    phone: str
    email: str
    specialties: str | None = None
    accepts_emergencies: bool = False
    services: list[PublicServiceSummary] = []

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: object) -> str:
        return str(v)


class ClinicFundingStats(BaseModel):
    """Funding statistics for a clinic."""

    clinic_id: str
    clinic_name: str
    total_funded_cents: int = 0
    donation_count: int = 0
    currency: str = "EUR"


class ClinicFundRequest(BaseModel):
    """Request to donate to a clinic fund."""

    clinic_id: str = Field(..., min_length=1)
    amount_cents: int = Field(..., ge=MINIMUM_DONATION_CENTS)
    currency: str = Field(default="EUR")
    service_id: str | None = Field(default=None)
    donor_name: str = Field(..., min_length=1, max_length=200)
    donor_email: EmailStr
    message: str | None = Field(default=None, max_length=500)

    @field_validator("currency", mode="before")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = str(v).upper()
        if v != "EUR":
            msg = "Only EUR donations are accepted for clinic funding."
            raise ValueError(msg)
        return v


class ClinicFundResponse(BaseModel):
    """Response after creating a clinic donation."""

    donation_id: str
    clinic_name: str
    donor_email: str
    amount_cents: int
    currency: str
    service_name: str | None = None
    stripe_checkout_url: str | None = None
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/clinics", response_model=PublicClinicListResponse)
async def list_public_clinics(
    city: str | None = Query(None, description="Filter by city"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> PublicClinicListResponse:
    """List active partner clinics (public, no auth)."""
    base = select(VetClinic).where(VetClinic.status == ClinicStatus.ACTIVE)
    if city:
        base = base.where(VetClinic.city.ilike(f"%{city}%"))

    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    rows_q = base.order_by(VetClinic.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(rows_q)
    clinics = result.scalars().all()

    return PublicClinicListResponse(
        items=[PublicClinicSummary.model_validate(c) for c in clinics],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/clinics/{clinic_id}", response_model=PublicClinicDetail)
async def get_public_clinic(
    clinic_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PublicClinicDetail:
    """Get clinic detail with active services (public, no auth)."""
    result = await db.execute(
        select(VetClinic).where(
            VetClinic.id == clinic_id,
            VetClinic.status == ClinicStatus.ACTIVE,
        )
    )
    clinic = result.scalar_one_or_none()
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found or not active.",
        )

    svc_result = await db.execute(
        select(ClinicService).where(
            ClinicService.clinic_id == clinic_id,
            ClinicService.is_active.is_(True),
        )
    )
    services = svc_result.scalars().all()

    detail = PublicClinicDetail.model_validate(clinic)
    detail.services = [PublicServiceSummary.model_validate(s) for s in services]
    return detail


@router.get("/clinics/{clinic_id}/stats", response_model=ClinicFundingStats)
async def get_clinic_funding_stats(
    clinic_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ClinicFundingStats:
    """Get funding stats for a clinic (total donated, count)."""
    # Verify clinic exists and is active
    result = await db.execute(
        select(VetClinic).where(
            VetClinic.id == clinic_id,
            VetClinic.status == ClinicStatus.ACTIVE,
        )
    )
    clinic = result.scalar_one_or_none()
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found or not active.",
        )

    # Aggregate donations for this clinic
    stats_q = select(
        func.coalesce(func.sum(Donation.amount_cents), 0).label("total"),
        func.count(Donation.id).label("count"),
    ).where(
        Donation.target_type == DonationTargetType.CLINIC,
        Donation.target_id == clinic_id,
    )
    stats_result = await db.execute(stats_q)
    row = stats_result.one()

    return ClinicFundingStats(
        clinic_id=str(clinic_id),
        clinic_name=clinic.name,
        total_funded_cents=row.total if isinstance(row.total, int) else int(str(row.total)),
        donation_count=row.count if isinstance(row.count, int) else int(str(row.count)),
    )


@router.post("/clinic-fund", response_model=ClinicFundResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic_fund_donation(
    body: ClinicFundRequest,
    db: AsyncSession = Depends(get_db),
) -> ClinicFundResponse:
    """Create a donation targeting a clinic (public, no auth)."""
    # 1. Validate clinic exists and is active
    result = await db.execute(
        select(VetClinic).where(
            VetClinic.id == UUID(body.clinic_id),
            VetClinic.status == ClinicStatus.ACTIVE,
        )
    )
    clinic = result.scalar_one_or_none()
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic not found or not active.",
        )

    # 2. Optionally validate service
    service_name: str | None = None
    if body.service_id:
        svc_result = await db.execute(
            select(ClinicService).where(
                ClinicService.id == UUID(body.service_id),
                ClinicService.clinic_id == UUID(body.clinic_id),
                ClinicService.is_active.is_(True),
            )
        )
        service = svc_result.scalar_one_or_none()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found or not active at this clinic.",
            )
        service_name = service.name

    # 3. Find or create donor
    donor_result = await db.execute(
        select(Donor).where(func.lower(Donor.email) == body.donor_email.lower())
    )
    donor = donor_result.scalar_one_or_none()
    if not donor:
        donor = Donor(
            full_name=body.donor_name,
            email=body.donor_email.lower(),
        )
        db.add(donor)
        await db.flush()

    # 4. Build notes
    notes_parts: list[str] = []
    if service_name:
        notes_parts.append(f"service={service_name}")
    if body.message:
        notes_parts.append(f"message={body.message}")
    notes = "; ".join(notes_parts) if notes_parts else None

    # 5. Create donation
    donation = Donation(
        donor_id=donor.id,
        amount_cents=body.amount_cents,
        currency=CurrencyCode.EUR,
        target_type=DonationTargetType.CLINIC,
        target_id=UUID(body.clinic_id),
        notes=notes,
    )
    db.add(donation)
    await db.flush()

    # 6. Stripe checkout (optional, graceful degradation)
    stripe_url: str | None = None
    try:
        import stripe

        from src.config import get_settings

        settings = get_settings()
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[
                    {
                        "price_data": {
                            "currency": "eur",
                            "unit_amount": body.amount_cents,
                            "product_data": {
                                "name": f"Donation to {clinic.name}",
                                "description": f"Clinic fund: {service_name or 'general'}",
                            },
                        },
                        "quantity": 1,
                    }
                ],
                customer_email=body.donor_email,
                metadata={
                    "donation_id": str(donation.id),
                    "clinic_id": body.clinic_id,
                    "service_id": body.service_id or "",
                },
                success_url=f"{settings.frontend_url}/clinics/thank-you?donation_id={donation.id}",
                cancel_url=f"{settings.frontend_url}/clinics/{body.clinic_id}/fund",
            )
            stripe_url = session.url
    except Exception:
        logger.warning("Stripe checkout session creation failed for clinic donation", exc_info=True)

    await db.commit()

    impact_msg = f"Your EUR {body.amount_cents / 100:.2f} helps {clinic.name}"
    if service_name:
        impact_msg += f" fund {service_name} services"
    impact_msg += ". Thank you!"

    return ClinicFundResponse(
        donation_id=str(donation.id),
        clinic_name=clinic.name,
        donor_email=body.donor_email,
        amount_cents=body.amount_cents,
        currency="EUR",
        service_name=service_name,
        stripe_checkout_url=stripe_url,
        message=impact_msg,
    )
