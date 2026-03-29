"""Donor retention and churn analysis service (RAP-258).

Computes live donor retention and churn metrics from the database.
Replaces the sample-data stubs that previously existed in donor_retention_analytics.py.

Metrics produced:
- Donor segment counts (new / active / at_risk / lapsed / churned)
- Retention rate and churn rate for a configurable lookback period
- Average donor lifetime in months (based on first-to-last donation span)
- Month-over-month cohort retention table

Segment thresholds (configurable via constants):
  NEW          — first donation within the lookback window
  ACTIVE       — donated within the last ACTIVE_THRESHOLD_DAYS
  AT_RISK      — last donation between ACTIVE_THRESHOLD_DAYS and LAPSED_THRESHOLD_DAYS
  LAPSED       — last donation between LAPSED_THRESHOLD_DAYS and CHURNED_THRESHOLD_DAYS
  CHURNED      — last donation > CHURNED_THRESHOLD_DAYS ago
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Integer

from src.db.models.donation import Donation, DonationStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Segment thresholds (days since last completed donation)
# ---------------------------------------------------------------------------

ACTIVE_THRESHOLD_DAYS: int = 90
LAPSED_THRESHOLD_DAYS: int = 180
CHURNED_THRESHOLD_DAYS: int = 365

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DonorSegmentCounts:
    """Donor count per lifecycle segment."""

    new: int
    active: int
    at_risk: int
    lapsed: int
    churned: int

    @property
    def total(self) -> int:
        return self.new + self.active + self.at_risk + self.lapsed + self.churned


@dataclass(frozen=True)
class RetentionMetrics:
    """Aggregate retention and churn metrics for a period."""

    period_days: int
    # Donors who donated both in the prior window AND in the current window
    retained_donors: int
    # Donors who donated in the prior window but NOT in the current window
    churned_donors: int
    # Donors whose first-ever donation falls in the current window
    new_donors: int
    # retention_rate = retained / (retained + churned), expressed as 0-100 %
    retention_rate_pct: float
    # churn_rate = churned / (retained + churned), expressed as 0-100 %
    churn_rate_pct: float
    # Segment breakdown at query time
    segments: DonorSegmentCounts
    generated_at: str


@dataclass(frozen=True)
class CohortRetentionRow:
    """Retention data for a single monthly cohort."""

    cohort_month: str  # e.g. "2025-01"
    cohort_size: int  # donors who first donated in this month
    retained_month_1: int  # still donated in month +1
    retained_month_3: int  # still donated in month +3
    retained_month_6: int  # still donated in month +6
    retention_pct_1: float
    retention_pct_3: float
    retention_pct_6: float


@dataclass(frozen=True)
class CohortRetentionResult:
    """Monthly cohort retention table."""

    generated_at: str
    lookback_months: int
    cohorts: list[CohortRetentionRow]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_rate(numerator: int, denominator: int) -> float:
    """Return percentage rate rounded to 1 decimal; 0.0 if denominator is zero."""
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 1)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_donor_segments(db: AsyncSession) -> DonorSegmentCounts:
    """Count donors by lifecycle segment based on last-donation recency.

    Uses the most recent completed donation date per donor to classify them.
    Donors with no completed donations are excluded.
    """
    now = datetime.now(UTC)
    active_cutoff = now - timedelta(days=ACTIVE_THRESHOLD_DAYS)
    lapsed_cutoff = now - timedelta(days=LAPSED_THRESHOLD_DAYS)
    churned_cutoff = now - timedelta(days=CHURNED_THRESHOLD_DAYS)

    # Subquery: last completed donation date per donor
    last_donation_sq = (
        select(
            Donation.donor_id.label("donor_id"),
            func.max(Donation.created_at).label("last_donated_at"),
            func.min(Donation.created_at).label("first_donated_at"),
        )
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.donor_id.is_not(None),
        )
        .group_by(Donation.donor_id)
        .subquery()
    )

    stmt = select(
        func.sum(
            cast(
                case(
                    (last_donation_sq.c.first_donated_at >= active_cutoff, 1),
                    else_=0,
                ),
                Integer,
            )
        ).label("new"),
        func.sum(
            cast(
                case(
                    (
                        (last_donation_sq.c.last_donated_at >= active_cutoff)
                        & (last_donation_sq.c.first_donated_at < active_cutoff),
                        1,
                    ),
                    else_=0,
                ),
                Integer,
            )
        ).label("active"),
        func.sum(
            cast(
                case(
                    (
                        (last_donation_sq.c.last_donated_at < active_cutoff)
                        & (last_donation_sq.c.last_donated_at >= lapsed_cutoff),
                        1,
                    ),
                    else_=0,
                ),
                Integer,
            )
        ).label("at_risk"),
        func.sum(
            cast(
                case(
                    (
                        (last_donation_sq.c.last_donated_at < lapsed_cutoff)
                        & (last_donation_sq.c.last_donated_at >= churned_cutoff),
                        1,
                    ),
                    else_=0,
                ),
                Integer,
            )
        ).label("lapsed"),
        func.sum(
            cast(
                case(
                    (last_donation_sq.c.last_donated_at < churned_cutoff, 1),
                    else_=0,
                ),
                Integer,
            )
        ).label("churned"),
    ).select_from(last_donation_sq)

    result = await db.execute(stmt)
    row = result.one()
    return DonorSegmentCounts(
        new=row.new or 0,
        active=row.active or 0,
        at_risk=row.at_risk or 0,
        lapsed=row.lapsed or 0,
        churned=row.churned or 0,
    )


async def get_retention_metrics(
    db: AsyncSession,
    period_days: int = 30,
) -> RetentionMetrics:
    """Compute donor retention and churn rates for a rolling period.

    Method:
    - prior window  = [now - 2*period_days, now - period_days)
    - current window = [now - period_days, now)
    - retained = donors who have a completed donation in BOTH windows
    - churned  = donors who have a completed donation in the prior window
                 but NOT in the current window
    - new = donors whose first-ever completed donation is in the current window

    Args:
        db: Async SQLAlchemy session.
        period_days: Length of each comparison window in days.

    Returns:
        RetentionMetrics with rates and segment counts.
    """
    now = datetime.now(UTC)
    current_start = now - timedelta(days=period_days)
    prior_start = now - timedelta(days=2 * period_days)

    # Donors in the prior window
    prior_stmt = (
        select(Donation.donor_id)
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.donor_id.is_not(None),
            Donation.created_at >= prior_start,
            Donation.created_at < current_start,
        )
        .distinct()
    )
    prior_result = await db.execute(prior_stmt)
    prior_donor_ids = {row[0] for row in prior_result}

    # Donors in the current window
    current_stmt = (
        select(Donation.donor_id)
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.donor_id.is_not(None),
            Donation.created_at >= current_start,
        )
        .distinct()
    )
    current_result = await db.execute(current_stmt)
    current_donor_ids = {row[0] for row in current_result}

    # New donors: first donation ever is in the current window
    first_donation_stmt = (
        select(Donation.donor_id)
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.donor_id.is_not(None),
        )
        .group_by(Donation.donor_id)
        .having(func.min(Donation.created_at) >= current_start)
    )
    new_result = await db.execute(first_donation_stmt)
    new_donor_ids = {row[0] for row in new_result}

    retained = len(prior_donor_ids & current_donor_ids)
    churned = len(prior_donor_ids - current_donor_ids)
    new_donors = len(new_donor_ids)
    denominator = retained + churned

    segments = await get_donor_segments(db)

    return RetentionMetrics(
        period_days=period_days,
        retained_donors=retained,
        churned_donors=churned,
        new_donors=new_donors,
        retention_rate_pct=_safe_rate(retained, denominator),
        churn_rate_pct=_safe_rate(churned, denominator),
        segments=segments,
        generated_at=datetime.now(UTC).isoformat(),
    )


async def get_cohort_retention(
    db: AsyncSession,
    lookback_months: int = 12,
) -> CohortRetentionResult:
    """Compute monthly cohort retention for the last N months.

    For each monthly cohort (donors whose first donation was in that month),
    reports how many also donated 1, 3, and 6 months later.

    Args:
        db: Async SQLAlchemy session.
        lookback_months: How many months of cohorts to include.

    Returns:
        CohortRetentionResult with one row per cohort month.
    """
    now = datetime.now(UTC)
    since = now - timedelta(days=lookback_months * 31)

    # Subquery: each donor's first completed donation month
    first_donation_sq = (
        select(
            Donation.donor_id.label("donor_id"),
            func.date_trunc("month", func.min(Donation.created_at)).label("cohort_month"),
        )
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.donor_id.is_not(None),
        )
        .group_by(Donation.donor_id)
        .subquery()
    )

    # Cohorts starting within lookback window
    cohort_stmt = (
        select(
            first_donation_sq.c.cohort_month,
            func.count(first_donation_sq.c.donor_id).label("cohort_size"),
        )
        .where(first_donation_sq.c.cohort_month >= since)
        .group_by(first_donation_sq.c.cohort_month)
        .order_by(first_donation_sq.c.cohort_month)
    )
    cohort_result = await db.execute(cohort_stmt)
    cohort_rows = cohort_result.all()

    rows: list[CohortRetentionRow] = []
    for cohort_row in cohort_rows:
        cohort_month = cohort_row.cohort_month
        cohort_size = cohort_row.cohort_size

        if not cohort_month or cohort_size == 0:
            continue

        # For each offset, count donors in this cohort who donated in that month
        retained_counts: dict[int, int] = {}
        for offset in (1, 3, 6):
            target_month_start = cohort_month + timedelta(days=offset * 31)
            target_month_end = target_month_start + timedelta(days=31)

            # Donors from this cohort who also donated in the target month
            retained_stmt = (
                select(func.count(func.distinct(Donation.donor_id)))
                .join(
                    first_donation_sq,
                    Donation.donor_id == first_donation_sq.c.donor_id,
                )
                .where(
                    first_donation_sq.c.cohort_month == cohort_month,
                    Donation.status == DonationStatus.COMPLETED,
                    Donation.created_at >= target_month_start,
                    Donation.created_at < target_month_end,
                )
            )
            retained_result = await db.execute(retained_stmt)
            retained_counts[offset] = retained_result.scalar_one() or 0

        cohort_label = (
            cohort_month.strftime("%Y-%m")
            if hasattr(cohort_month, "strftime")
            else str(cohort_month)[:7]
        )

        rows.append(
            CohortRetentionRow(
                cohort_month=cohort_label,
                cohort_size=cohort_size,
                retained_month_1=retained_counts[1],
                retained_month_3=retained_counts[3],
                retained_month_6=retained_counts[6],
                retention_pct_1=_safe_rate(retained_counts[1], cohort_size),
                retention_pct_3=_safe_rate(retained_counts[3], cohort_size),
                retention_pct_6=_safe_rate(retained_counts[6], cohort_size),
            )
        )

    return CohortRetentionResult(
        generated_at=datetime.now(UTC).isoformat(),
        lookback_months=lookback_months,
        cohorts=rows,
    )
