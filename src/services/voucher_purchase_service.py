"""Service for voucher purchase flow.

Handles voucher purchase requests from donors: validates clinic/service,
calculates pricing, creates voucher records, and generates purchase
summaries for confirmation emails.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.clinic_service import ClinicService
from src.db.models.vet_voucher import VetVoucher, VoucherStatus
from src.services.vet_voucher_service import generate_voucher_code

logger = logging.getLogger(__name__)

# Default voucher validity in days from purchase
DEFAULT_VOUCHER_VALIDITY_DAYS = 90

# Purchase limits
MIN_QUANTITY = 1
MAX_QUANTITY = 100


class ClinicServiceNotFoundError(Exception):
    """Raised when a clinic service is not found or not active."""

    def __init__(self, service_id: UUID) -> None:
        self.service_id = service_id
        self.message = f"Clinic service {service_id} not found or not active."
        super().__init__(self.message)


class InvalidQuantityError(Exception):
    """Raised when purchase quantity is out of range."""

    def __init__(self, quantity: int) -> None:
        self.quantity = quantity
        self.message = (
            f"Quantity {quantity} is invalid. Must be between {MIN_QUANTITY} and {MAX_QUANTITY}."
        )
        super().__init__(self.message)


@dataclass
class VoucherPurchaseRequest:
    """Data for a voucher purchase."""

    donor_id: UUID
    clinic_id: UUID
    service_id: UUID
    quantity: int
    payment_method: str  # "stripe" or "sepa"
    validity_days: int = DEFAULT_VOUCHER_VALIDITY_DAYS


@dataclass
class PurchasePriceBreakdown:
    """Price breakdown for a voucher purchase."""

    service_name: str
    service_category: str
    unit_price_pyg: int
    unit_price_eur: float | None
    quantity: int
    total_pyg: int
    total_eur: float | None


@dataclass
class VoucherPurchaseResult:
    """Result of a successful voucher purchase."""

    voucher_ids: list[UUID]
    voucher_codes: list[str]
    total_pyg: int
    total_eur: float | None
    quantity: int
    clinic_id: UUID
    service_id: UUID
    service_name: str
    expires_at: datetime


async def get_service_for_purchase(db: AsyncSession, service_id: UUID) -> ClinicService:
    """Fetch and validate a clinic service for purchase.

    Raises ClinicServiceNotFoundError if the service doesn't exist or is inactive.
    """
    result = await db.execute(
        select(ClinicService).where(
            ClinicService.id == service_id,
            ClinicService.is_active.is_(True),
        )
    )
    service = result.scalar_one_or_none()
    if service is None:
        raise ClinicServiceNotFoundError(service_id)
    return service


def calculate_purchase_price(
    service: ClinicService,
    quantity: int,
) -> PurchasePriceBreakdown:
    """Calculate the total price for a voucher purchase.

    Validates quantity and returns a price breakdown.
    """
    if quantity < MIN_QUANTITY or quantity > MAX_QUANTITY:
        raise InvalidQuantityError(quantity)

    total_pyg = service.price_pyg * quantity
    total_eur = float(service.price_eur) * quantity if service.price_eur is not None else None

    return PurchasePriceBreakdown(
        service_name=service.name,
        service_category=service.category,
        unit_price_pyg=service.price_pyg,
        unit_price_eur=float(service.price_eur) if service.price_eur is not None else None,
        quantity=quantity,
        total_pyg=total_pyg,
        total_eur=total_eur,
    )


async def create_vouchers_for_purchase(
    db: AsyncSession,
    request: VoucherPurchaseRequest,
    service: ClinicService,
) -> VoucherPurchaseResult:
    """Create voucher records for a completed purchase.

    Creates N individual vouchers (one per unit), each with a unique code.
    All vouchers share the same donor, clinic, service, and expiry.
    """
    if request.quantity < MIN_QUANTITY or request.quantity > MAX_QUANTITY:
        raise InvalidQuantityError(request.quantity)

    now = datetime.now(UTC)
    expires_at = now + timedelta(days=request.validity_days)

    voucher_ids: list[UUID] = []
    voucher_codes: list[str] = []

    for _ in range(request.quantity):
        code = generate_voucher_code()
        voucher = VetVoucher(
            code=code,
            amount_pyg=service.price_pyg,
            amount_eur=float(service.price_eur) if service.price_eur is not None else None,
            donor_id=request.donor_id,
            clinic_id=request.clinic_id,
            service_id=service.id,
            service_category=service.category,
            status=VoucherStatus.PURCHASED,
            purchased_at=now,
            expires_at=expires_at,
        )
        db.add(voucher)
        await db.flush()
        await db.refresh(voucher)
        voucher_ids.append(voucher.id)
        voucher_codes.append(code)

    logger.info(
        "Created %d vouchers for donor %s at clinic %s (service=%s, total=%d PYG)",
        request.quantity,
        request.donor_id,
        request.clinic_id,
        service.name,
        service.price_pyg * request.quantity,
    )

    return VoucherPurchaseResult(
        voucher_ids=voucher_ids,
        voucher_codes=voucher_codes,
        total_pyg=service.price_pyg * request.quantity,
        total_eur=(
            float(service.price_eur) * request.quantity if service.price_eur is not None else None
        ),
        quantity=request.quantity,
        clinic_id=request.clinic_id,
        service_id=service.id,
        service_name=service.name,
        expires_at=expires_at,
    )


async def get_donor_vouchers(
    db: AsyncSession,
    donor_id: UUID,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[VetVoucher], int]:
    """List vouchers purchased by a donor.

    Used for the donor's voucher wallet view.
    """
    from sqlalchemy import func

    query = select(VetVoucher).where(VetVoucher.donor_id == donor_id)
    count_query = select(func.count(VetVoucher.id)).where(VetVoucher.donor_id == donor_id)

    if status:
        query = query.where(VetVoucher.status == status)
        count_query = count_query.where(VetVoucher.status == status)

    query = (
        query.order_by(VetVoucher.purchased_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    vouchers = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    return vouchers, total
