"""Voucher financial reconciliation service.

Provides aggregation queries for the admin voucher finance dashboard:
summary stats, per-clinic breakdowns, clinic detail views, and
monthly settlement reports.
"""

import logging
from collections import defaultdict
from datetime import UTC, date, datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.vet_clinic import VetClinic
from src.db.models.vet_voucher import VetVoucher, VoucherStatus
from src.schemas.voucher_finance import (
    ClinicDetailResponse,
    ClinicFinanceListResponse,
    ClinicFinanceRow,
    MonthlySettlementRow,
    SettlementReportResponse,
    VoucherDetailRow,
    VoucherFinanceSummary,
)

logger = logging.getLogger(__name__)

# Statuses considered "active" (not yet terminal)
ACTIVE_STATUSES = {VoucherStatus.PURCHASED, VoucherStatus.ASSIGNED}


async def get_finance_summary(db: AsyncSession) -> VoucherFinanceSummary:
    """Return aggregate financial stats across the entire voucher program."""
    # Count by status
    status_counts_q = sa.select(
        VetVoucher.status,
        sa.func.count().label("cnt"),
        sa.func.coalesce(sa.func.sum(VetVoucher.amount_pyg), 0).label("sum_pyg"),
        sa.func.coalesce(sa.func.sum(VetVoucher.amount_eur), 0.0).label("sum_eur"),
    ).group_by(VetVoucher.status)

    result = await db.execute(status_counts_q)
    rows = result.all()

    counts: dict[str, int] = defaultdict(int)
    sums_pyg: dict[str, int] = defaultdict(int)
    sums_eur: dict[str, float] = defaultdict(float)

    for row in rows:
        counts[row.status] = row.cnt
        sums_pyg[row.status] = int(row.sum_pyg)
        sums_eur[row.status] = float(row.sum_eur)

    total_purchased = sum(counts.values())
    total_redeemed = counts.get(VoucherStatus.REDEEMED, 0)
    total_expired = counts.get(VoucherStatus.EXPIRED, 0)
    total_cancelled = counts.get(VoucherStatus.CANCELLED, 0)
    total_active = counts.get(VoucherStatus.PURCHASED, 0) + counts.get(VoucherStatus.ASSIGNED, 0)

    # Redemption rate: redeemed / (redeemed + expired + active)
    denominator = total_redeemed + total_expired + total_active
    redemption_rate = (total_redeemed / denominator * 100) if denominator > 0 else 0.0

    total_collected_pyg = sum(sums_pyg.values())
    total_collected_eur = sum(sums_eur.values())
    total_owed_pyg = sums_pyg.get(VoucherStatus.REDEEMED, 0)

    return VoucherFinanceSummary(
        total_purchased=total_purchased,
        total_redeemed=total_redeemed,
        total_expired=total_expired,
        total_cancelled=total_cancelled,
        total_active=total_active,
        redemption_rate_pct=round(redemption_rate, 2),
        total_collected_pyg=total_collected_pyg,
        total_owed_to_clinics_pyg=total_owed_pyg,
        total_collected_eur=round(total_collected_eur, 2),
    )


async def get_clinic_breakdown(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    sort_by: str = "clinic_name",
    sort_dir: str = "asc",
) -> ClinicFinanceListResponse:
    """Return paginated per-clinic financial breakdown.

    Only includes clinics that have at least one voucher redeemed at them.
    """
    # Base: all redeemed vouchers grouped by redeemed_clinic_id
    redeemed_q = (
        sa.select(
            VetVoucher.redeemed_clinic_id.label("clinic_id"),
            sa.func.count().label("redeemed_count"),
            sa.func.coalesce(sa.func.sum(VetVoucher.amount_pyg), 0).label("redeemed_pyg"),
            sa.func.coalesce(sa.func.sum(VetVoucher.amount_eur), 0.0).label("redeemed_eur"),
        )
        .where(VetVoucher.status == VoucherStatus.REDEEMED)
        .where(VetVoucher.redeemed_clinic_id.isnot(None))
        .group_by(VetVoucher.redeemed_clinic_id)
    ).subquery("redeemed")

    # Active vouchers restricted to specific clinic
    active_q = (
        sa.select(
            VetVoucher.clinic_id.label("clinic_id"),
            sa.func.count().label("active_count"),
        )
        .where(VetVoucher.status.in_(list(ACTIVE_STATUSES)))
        .where(VetVoucher.clinic_id.isnot(None))
        .group_by(VetVoucher.clinic_id)
    ).subquery("active")

    # Expired vouchers restricted to specific clinic
    expired_q = (
        sa.select(
            VetVoucher.clinic_id.label("clinic_id"),
            sa.func.count().label("expired_count"),
        )
        .where(VetVoucher.status == VoucherStatus.EXPIRED)
        .where(VetVoucher.clinic_id.isnot(None))
        .group_by(VetVoucher.clinic_id)
    ).subquery("expired")

    # Join with clinics
    base_q = (
        sa.select(
            VetClinic.id.label("clinic_id"),
            VetClinic.name.label("clinic_name"),
            sa.func.coalesce(redeemed_q.c.redeemed_count, 0).label("redeemed_vouchers"),
            sa.func.coalesce(redeemed_q.c.redeemed_pyg, 0).label("amount_redeemed_pyg"),
            sa.func.coalesce(redeemed_q.c.redeemed_eur, 0.0).label("amount_redeemed_eur"),
            sa.func.coalesce(active_q.c.active_count, 0).label("active_vouchers"),
            sa.func.coalesce(expired_q.c.expired_count, 0).label("expired_vouchers"),
        )
        .outerjoin(redeemed_q, redeemed_q.c.clinic_id == VetClinic.id)
        .outerjoin(active_q, active_q.c.clinic_id == VetClinic.id)
        .outerjoin(expired_q, expired_q.c.clinic_id == VetClinic.id)
    )

    if search:
        base_q = base_q.where(VetClinic.name.ilike(f"%{search}%"))

    # Count total
    count_q = sa.select(sa.func.count()).select_from(base_q.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Sorting
    sort_columns = {
        "clinic_name": VetClinic.name,
        "redeemed_vouchers": sa.text("redeemed_vouchers"),
        "amount_redeemed_pyg": sa.text("amount_redeemed_pyg"),
        "active_vouchers": sa.text("active_vouchers"),
    }
    sort_col = sort_columns.get(sort_by, VetClinic.name)
    order = sa.desc(sort_col) if sort_dir == "desc" else sa.asc(sort_col)

    # Paginate
    offset = (page - 1) * page_size
    paginated_q = base_q.order_by(order).offset(offset).limit(page_size)

    result = await db.execute(paginated_q)
    rows = result.all()

    items = [
        ClinicFinanceRow(
            clinic_id=row.clinic_id,
            clinic_name=row.clinic_name,
            active_vouchers=row.active_vouchers,
            redeemed_vouchers=row.redeemed_vouchers,
            expired_vouchers=row.expired_vouchers,
            amount_redeemed_pyg=int(row.amount_redeemed_pyg),
            amount_redeemed_eur=round(float(row.amount_redeemed_eur), 2),
        )
        for row in rows
    ]

    return ClinicFinanceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_clinic_detail(
    db: AsyncSession,
    clinic_id: UUID,
) -> ClinicDetailResponse | None:
    """Return detailed voucher breakdown for a single clinic."""
    # Get clinic
    clinic_q = sa.select(VetClinic).where(VetClinic.id == clinic_id)
    clinic = (await db.execute(clinic_q)).scalar_one_or_none()
    if clinic is None:
        return None

    # Get all vouchers redeemed at this clinic OR restricted to this clinic
    vouchers_q = (
        sa.select(VetVoucher)
        .where(
            sa.or_(
                VetVoucher.redeemed_clinic_id == clinic_id,
                VetVoucher.clinic_id == clinic_id,
            )
        )
        .order_by(VetVoucher.purchased_at.desc())
    )
    result = await db.execute(vouchers_q)
    vouchers = result.scalars().all()

    total_redeemed_pyg = 0
    total_redeemed_eur = 0.0
    redeemed_count = 0
    active_count = 0
    expired_count = 0
    voucher_details = []

    for v in vouchers:
        if v.status == VoucherStatus.REDEEMED and v.redeemed_clinic_id == clinic_id:
            total_redeemed_pyg += v.amount_pyg
            total_redeemed_eur += float(v.amount_eur or 0)
            redeemed_count += 1
        elif v.status in ACTIVE_STATUSES:
            active_count += 1
        elif v.status == VoucherStatus.EXPIRED:
            expired_count += 1

        voucher_details.append(
            VoucherDetailRow(
                voucher_id=v.id,
                code=v.code,
                status=v.status,
                amount_pyg=v.amount_pyg,
                amount_eur=float(v.amount_eur) if v.amount_eur else None,
                donor_id=v.donor_id,
                purchased_at=v.purchased_at,
                redeemed_at=v.redeemed_at,
                expires_at=v.expires_at,
            )
        )

    return ClinicDetailResponse(
        clinic_id=clinic.id,
        clinic_name=clinic.name,
        total_redeemed_pyg=total_redeemed_pyg,
        total_redeemed_eur=round(total_redeemed_eur, 2),
        redeemed_count=redeemed_count,
        active_count=active_count,
        expired_count=expired_count,
        vouchers=voucher_details,
    )


async def get_settlement_report(
    db: AsyncSession,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> SettlementReportResponse:
    """Return monthly settlement report for redeemed vouchers.

    Groups redeemed vouchers by month and returns totals.
    """
    if end_date is None:
        end_date = datetime.now(UTC).date()
    if start_date is None:
        # Default to 12 months back
        start_date = date(end_date.year - 1, end_date.month, end_date.day)

    # Query redeemed vouchers in date range, grouped by month
    month_expr = sa.func.to_char(VetVoucher.redeemed_at, "YYYY-MM")

    q = (
        sa.select(
            month_expr.label("month"),
            sa.func.count().label("cnt"),
            sa.func.coalesce(sa.func.sum(VetVoucher.amount_pyg), 0).label("sum_pyg"),
            sa.func.coalesce(sa.func.sum(VetVoucher.amount_eur), 0.0).label("sum_eur"),
        )
        .where(VetVoucher.status == VoucherStatus.REDEEMED)
        .where(VetVoucher.redeemed_at.isnot(None))
        .where(sa.func.date(VetVoucher.redeemed_at) >= start_date)
        .where(sa.func.date(VetVoucher.redeemed_at) <= end_date)
        .group_by(month_expr)
        .order_by(month_expr)
    )

    result = await db.execute(q)
    rows_data = result.all()

    monthly_rows = []
    grand_total_pyg = 0
    grand_total_eur = 0.0

    for row in rows_data:
        pyg = int(row.sum_pyg)
        eur = round(float(row.sum_eur), 2)
        grand_total_pyg += pyg
        grand_total_eur += eur
        monthly_rows.append(
            MonthlySettlementRow(
                month=row.month,
                total_redeemed_count=row.cnt,
                total_redeemed_pyg=pyg,
                total_redeemed_eur=eur,
            )
        )

    return SettlementReportResponse(
        start_date=start_date,
        end_date=end_date,
        rows=monthly_rows,
        total_redeemed_pyg=grand_total_pyg,
        total_redeemed_eur=round(grand_total_eur, 2),
    )


def format_settlement_csv(report: SettlementReportResponse) -> str:
    """Format a settlement report as CSV string."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Month",
            "Total Redeemed",
            "Amount (PYG)",
            "Amount (EUR)",
        ]
    )
    for row in report.rows:
        writer.writerow(
            [
                row.month,
                row.total_redeemed_count,
                row.total_redeemed_pyg,
                row.total_redeemed_eur,
            ]
        )
    # Grand total row
    writer.writerow(
        [
            "TOTAL",
            sum(r.total_redeemed_count for r in report.rows),
            report.total_redeemed_pyg,
            report.total_redeemed_eur,
        ]
    )

    return output.getvalue()
