"""Admin API for batch tax receipt generation and email delivery.

Provides a single admin-only endpoint to trigger year-end annual receipt
emails for all donors with completed donations in a given year.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.config import get_settings
from src.db.models.donation import Donation, DonationStatus, Donor
from src.db.models.user import User
from src.db.session import get_db
from src.services.annual_donation_summary_service import DonationLineItem
from src.services.batch_receipt_service import BatchReceiptService, DonorReceiptInput

router = APIRouter(prefix="/admin", tags=["batch-receipts"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class BatchReceiptResponse(BaseModel):
    """Response for a batch receipt generation run."""

    year: int
    total_donors: int
    sent: int
    dry_run_would_send: int
    failed: int
    skipped_no_email: int
    success: bool
    errors: list[dict[str, Any]]
    started_at: datetime
    finished_at: datetime | None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/batch-receipts/{year}",
    response_model=BatchReceiptResponse,
    summary="Send annual donation summary receipts to all donors for a given year",
    description=(
        "Generates and emails annual donation summary PDFs for every donor "
        "that has at least one completed donation in the requested year. "
        "When SMTP is disabled (smtp_enabled=False), the endpoint runs in "
        "dry-run mode: PDFs are generated but not sent, and "
        "dry_run_would_send is incremented instead of sent."
    ),
)
async def trigger_batch_receipts(
    year: int,
    dry_run: bool = Query(
        default=False,
        description="If true, generate PDFs but do not send emails regardless of SMTP config.",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> BatchReceiptResponse:
    # 1 — load all donors with completed donations in the requested year
    stmt = (
        select(
            Donor,
            Donation,
        )
        .join(Donation, Donation.donor_id == Donor.id)
        .where(
            Donation.status == DonationStatus.COMPLETED,
            extract("year", Donation.created_at) == year,
        )
        .order_by(Donor.id, Donation.created_at)
    )
    rows = (await db.execute(stmt)).all()

    # 2 — group donations by donor
    donors_map: dict[Any, tuple[Donor, list[Donation]]] = {}
    for donor, donation in rows:
        if donor.id not in donors_map:
            donors_map[donor.id] = (donor, [])
        donors_map[donor.id][1].append(donation)

    # 3 — build DonorReceiptInput list
    donor_inputs: list[DonorReceiptInput] = []
    for donor, donations in donors_map.values():
        totals: dict[str, int] = {}
        line_items: list[DonationLineItem] = []
        for d in donations:
            totals[d.currency] = totals.get(d.currency, 0) + d.amount_cents
            line_items.append(
                DonationLineItem(
                    donation_id=d.id,
                    date=d.created_at,
                    amount_cents=d.amount_cents,
                    currency=d.currency,
                    payment_method=d.payment_method,
                    fund_category=d.fund_category,
                    receipt_number=d.receipt_number,
                )
            )
        donor_inputs.append(
            DonorReceiptInput(
                donor_id=donor.id,
                donor_name=donor.full_name,
                donor_email=donor.email if donor.email else None,
                donor_country=donor.country,
                donations=line_items,
                totals_by_currency=totals,
            )
        )

    # 4 — build settings, optionally override smtp_enabled for dry-run
    settings = get_settings()
    if dry_run:
        settings = settings.model_copy(update={"smtp_enabled": False})

    # 5 — run batch
    svc = BatchReceiptService(settings)
    result = await svc.run(year=year, donors=donor_inputs)

    return BatchReceiptResponse(
        year=result.year,
        total_donors=result.total_donors,
        sent=result.sent,
        dry_run_would_send=result.dry_run_would_send,
        failed=result.failed,
        skipped_no_email=result.skipped_no_email,
        success=result.success,
        errors=result.errors,
        started_at=result.started_at,
        finished_at=result.finished_at or datetime.now(UTC),
    )
