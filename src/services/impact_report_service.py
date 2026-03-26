"""Service layer for generating shelter impact reports.

Aggregates data from animals, adoptions, donations, and in-kind donations
into a structured report for donor transparency and stakeholder reporting.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal
from src.db.models.donation import Donation, DonationStatus
from src.db.models.in_kind_donation import InKindDonation
from src.schemas.impact_report import (
    AdoptionStats,
    AnimalStats,
    CurrencyTotal,
    DonationStats,
    ImpactReport,
    InKindCategoryTotal,
    InKindStats,
    SpeciesCount,
    StatusCount,
)


async def _get_animal_stats(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> AnimalStats:
    """Aggregate animal statistics for the report period."""
    # Total animals currently in system
    total_q = await db.execute(select(func.count()).select_from(Animal))
    total_animals = total_q.scalar_one()

    # New intakes within the date range
    intakes_q = await db.execute(
        select(func.count())
        .select_from(Animal)
        .where(
            Animal.created_at >= start_date,
            Animal.created_at <= end_date,
        )
    )
    new_intakes = intakes_q.scalar_one()

    # By species
    species_q = await db.execute(
        select(Animal.species, func.count().label("cnt"))
        .group_by(Animal.species)
        .order_by(func.count().desc())
    )
    by_species = [SpeciesCount(species=row.species, count=row.cnt) for row in species_q]

    # By status
    status_q = await db.execute(
        select(Animal.status, func.count().label("cnt"))
        .group_by(Animal.status)
        .order_by(func.count().desc())
    )
    by_status = [StatusCount(status=row.status, count=row.cnt) for row in status_q]

    return AnimalStats(
        total_animals=total_animals,
        new_intakes=new_intakes,
        by_species=by_species,
        by_status=by_status,
    )


async def _get_adoption_stats(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> AdoptionStats:
    """Aggregate adoption request statistics for the report period."""
    base_filter = [
        AdoptionRequest.created_at >= start_date,
        AdoptionRequest.created_at <= end_date,
    ]

    total_q = await db.execute(
        select(func.count()).select_from(AdoptionRequest).where(*base_filter)
    )
    total_requests = total_q.scalar_one()

    approved_q = await db.execute(
        select(func.count())
        .select_from(AdoptionRequest)
        .where(
            *base_filter,
            AdoptionRequest.status == AdoptionRequestStatus.APPROVED.value,
        )
    )
    approved = approved_q.scalar_one()

    rejected_q = await db.execute(
        select(func.count())
        .select_from(AdoptionRequest)
        .where(
            *base_filter,
            AdoptionRequest.status == AdoptionRequestStatus.REJECTED.value,
        )
    )
    rejected = rejected_q.scalar_one()

    pending_q = await db.execute(
        select(func.count())
        .select_from(AdoptionRequest)
        .where(
            *base_filter,
            AdoptionRequest.status == AdoptionRequestStatus.PENDING.value,
        )
    )
    pending = pending_q.scalar_one()

    approval_rate = round(approved / total_requests * 100, 1) if total_requests > 0 else 0.0

    return AdoptionStats(
        total_requests=total_requests,
        approved=approved,
        rejected=rejected,
        pending=pending,
        approval_rate_pct=approval_rate,
    )


async def _get_donation_stats(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> DonationStats:
    """Aggregate monetary donation statistics for the report period."""
    base_filter = [
        Donation.created_at >= start_date,
        Donation.created_at <= end_date,
        Donation.status == DonationStatus.COMPLETED.value,
    ]

    # Total completed donations
    total_q = await db.execute(select(func.count()).select_from(Donation).where(*base_filter))
    total_completed = total_q.scalar_one()

    # By currency
    currency_q = await db.execute(
        select(
            Donation.currency,
            func.coalesce(func.sum(Donation.amount_cents), 0).label("total_cents"),
            func.count().label("donation_count"),
        )
        .where(*base_filter)
        .group_by(Donation.currency)
        .order_by(func.sum(Donation.amount_cents).desc())
    )
    total_by_currency = [
        CurrencyTotal(
            currency=row.currency,
            total_cents=row.total_cents,
            donation_count=row.donation_count,
        )
        for row in currency_q
    ]

    # Unique donors (excluding anonymous)
    donors_q = await db.execute(
        select(func.count(func.distinct(Donation.donor_id))).where(
            *base_filter,
            Donation.donor_id.isnot(None),
        )
    )
    unique_donors = donors_q.scalar_one()

    return DonationStats(
        total_completed=total_completed,
        total_by_currency=total_by_currency,
        unique_donors=unique_donors,
    )


async def _get_in_kind_stats(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> InKindStats:
    """Aggregate in-kind donation statistics for the report period."""
    base_filter = [
        InKindDonation.created_at >= start_date,
        InKindDonation.created_at <= end_date,
    ]

    total_q = await db.execute(select(func.count()).select_from(InKindDonation).where(*base_filter))
    total_donations = total_q.scalar_one()

    category_q = await db.execute(
        select(
            InKindDonation.item_type,
            func.count().label("cnt"),
            func.coalesce(func.sum(InKindDonation.estimated_value_cents), 0).label("value_cents"),
        )
        .where(*base_filter)
        .group_by(InKindDonation.item_type)
        .order_by(func.count().desc())
    )
    by_category = [
        InKindCategoryTotal(
            category=row.category,
            count=row.cnt,
            estimated_value_cents=row.value_cents,
        )
        for row in category_q
    ]

    return InKindStats(
        total_donations=total_donations,
        by_category=by_category,
    )


async def generate_impact_report(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
) -> ImpactReport:
    """Generate a full shelter impact report for the given date range."""
    animals = await _get_animal_stats(db, start_date, end_date)
    adoptions = await _get_adoption_stats(db, start_date, end_date)
    donations = await _get_donation_stats(db, start_date, end_date)
    in_kind = await _get_in_kind_stats(db, start_date, end_date)

    return ImpactReport(
        report_title="Refugio Animal Paraguay — Impact Report",
        start_date=start_date,
        end_date=end_date,
        generated_at=datetime.now(UTC),
        animals=animals,
        adoptions=adoptions,
        donations=donations,
        in_kind=in_kind,
    )
