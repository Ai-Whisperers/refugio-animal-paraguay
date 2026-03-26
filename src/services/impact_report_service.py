"""Impact report service for aggregating shelter performance metrics.

Generates structured impact data for a given date range, covering:
animals served, adoptions by species, donations by currency, fund
allocation breakdown, cost-per-adoption, and time-to-adoption metrics.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal
from src.db.models.donation import Donation, DonationStatus
from src.db.models.fund_allocation import FundAllocation
from src.db.models.in_kind_donation import InKindDonation


async def count_animals_served(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Count animals that entered the shelter in the date range.

    Returns dict with total count and breakdown by species.
    """
    query = (
        select(
            Animal.species,
            func.count(Animal.id).label("count"),
        )
        .where(
            Animal.created_at >= start_date,
            Animal.created_at <= end_date,
        )
        .group_by(Animal.species)
    )

    result = await db.execute(query)
    rows = result.all()

    by_species = {row.species: row.count for row in rows}
    total = sum(by_species.values())

    return {"total": total, "by_species": by_species}


async def count_adoptions(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Count completed adoptions in the date range.

    Returns total count and breakdown by animal species.
    """
    query = (
        select(
            Animal.species,
            func.count(AdoptionRequest.id).label("count"),
        )
        .join(Animal, AdoptionRequest.animal_id == Animal.id)
        .where(
            AdoptionRequest.status == AdoptionRequestStatus.APPROVED,
            AdoptionRequest.updated_at >= start_date,
            AdoptionRequest.updated_at <= end_date,
        )
        .group_by(Animal.species)
    )

    result = await db.execute(query)
    rows = result.all()

    by_species = {row.species: row.count for row in rows}
    total = sum(by_species.values())

    return {"total": total, "by_species": by_species}


async def sum_donations(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Sum completed donations in the date range by currency.

    Returns total_count, totals_by_currency (in cents), and donation_count_by_method.
    """
    # By currency
    currency_query = (
        select(
            Donation.currency,
            func.sum(Donation.amount_cents).label("total_cents"),
            func.count(Donation.id).label("count"),
        )
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.created_at >= start_date,
            Donation.created_at <= end_date,
        )
        .group_by(Donation.currency)
    )

    result = await db.execute(currency_query)
    rows = result.all()

    by_currency = {}
    total_count = 0
    for row in rows:
        by_currency[row.currency] = {
            "total_cents": row.total_cents,
            "count": row.count,
        }
        total_count += row.count

    # By payment method
    method_query = (
        select(
            Donation.payment_method,
            func.count(Donation.id).label("count"),
        )
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.created_at >= start_date,
            Donation.created_at <= end_date,
        )
        .group_by(Donation.payment_method)
    )

    method_result = await db.execute(method_query)
    by_method = {row.payment_method: row.count for row in method_result.all()}

    return {
        "total_count": total_count,
        "by_currency": by_currency,
        "by_payment_method": by_method,
    }


async def sum_in_kind_donations(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Count and summarize in-kind donations in the date range."""
    query = (
        select(
            InKindDonation.item_type,
            func.count(InKindDonation.id).label("count"),
        )
        .where(
            InKindDonation.created_at >= start_date,
            InKindDonation.created_at <= end_date,
        )
        .group_by(InKindDonation.item_type)
    )

    result = await db.execute(query)
    rows = result.all()

    by_type = {row.item_type: row.count for row in rows}
    total = sum(by_type.values())

    return {"total": total, "by_type": by_type}


async def get_fund_allocation_breakdown(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> dict:
    """Get fund allocation breakdown by category for the date range.

    Returns total_cents and breakdown with percentage per category.
    """
    query = (
        select(
            FundAllocation.category,
            func.sum(FundAllocation.amount_cents).label("total_cents"),
            func.count(FundAllocation.id).label("count"),
        )
        .where(
            FundAllocation.transaction_date >= start_date,
            FundAllocation.transaction_date <= end_date,
        )
        .group_by(FundAllocation.category)
        .order_by(func.sum(FundAllocation.amount_cents).desc())
    )

    result = await db.execute(query)
    rows = result.all()

    grand_total = sum(row.total_cents for row in rows) if rows else 0

    breakdown = []
    for row in rows:
        pct = round(row.total_cents / grand_total * 100, 2) if grand_total > 0 else 0.0
        breakdown.append(
            {
                "category": row.category,
                "total_cents": row.total_cents,
                "transaction_count": row.count,
                "percentage": pct,
            }
        )

    return {"total_cents": grand_total, "breakdown": breakdown}


async def calculate_avg_time_to_adoption(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> float | None:
    """Calculate average days from animal creation to adoption approval.

    Returns average days or None if no adoptions in the range.
    """
    # Get approved adoption requests in range, joined with animal created_at
    query = (
        select(
            func.avg(
                func.extract(
                    "epoch",
                    AdoptionRequest.updated_at - Animal.created_at,
                )
                / 86400  # Convert seconds to days
            ).label("avg_days")
        )
        .join(Animal, AdoptionRequest.animal_id == Animal.id)
        .where(
            AdoptionRequest.status == AdoptionRequestStatus.APPROVED,
            AdoptionRequest.updated_at >= start_date,
            AdoptionRequest.updated_at <= end_date,
        )
    )

    result = await db.execute(query)
    avg_days = result.scalar()

    return round(float(avg_days), 1) if avg_days is not None else None


async def generate_impact_report(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    generated_by_user_id: UUID | None = None,
) -> dict:
    """Generate a full impact report for the given date range.

    Aggregates all metrics into a single structured response.
    """
    animals = await count_animals_served(db, start_date, end_date)
    adoptions = await count_adoptions(db, start_date, end_date)
    donations = await sum_donations(db, start_date, end_date)
    in_kind = await sum_in_kind_donations(db, start_date, end_date)
    fund_allocation = await get_fund_allocation_breakdown(db, start_date, end_date)
    avg_time = await calculate_avg_time_to_adoption(db, start_date, end_date)

    # Cost per adoption: total fund allocation / number of adoptions
    cost_per_adoption_cents = None
    if adoptions["total"] > 0 and fund_allocation["total_cents"] > 0:
        cost_per_adoption_cents = round(
            fund_allocation["total_cents"] / adoptions["total"]
        )

    return {
        "report_metadata": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "generated_by_user_id": str(generated_by_user_id) if generated_by_user_id else None,
        },
        "animals_served": animals,
        "adoptions": adoptions,
        "donations": donations,
        "in_kind_donations": in_kind,
        "fund_allocation": fund_allocation,
        "performance_metrics": {
            "avg_time_to_adoption_days": avg_time,
            "cost_per_adoption_cents": cost_per_adoption_cents,
        },
    }
