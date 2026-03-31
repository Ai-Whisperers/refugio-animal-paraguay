"""Portal dashboard service.

Aggregates user-specific data from multiple tables to build the unified
personal dashboard. Matches user to adopter/donor profiles by email.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest
from src.db.models.animal import Animal
from src.db.models.donation import Donation, DonationStatus, Donor
from src.db.models.sponsorship import Sponsorship, SponsorshipStatus, SponsorshipTier
from src.db.models.user import User

logger = logging.getLogger(__name__)

# Limits for dashboard queries
MAX_APPLICATIONS = 5
MAX_SPONSORED_ANIMALS = 10

# -- Data structures returned by the service ----------------------------------


class ApplicationDetail:
    """Full adoption application info for the adopter-focused status page."""

    __slots__ = (
        "animal_id",
        "animal_name",
        "animal_species",
        "decided_at",
        "id",
        "notes",
        "status",
        "submitted_at",
    )

    def __init__(
        self,
        id: UUID,
        animal_id: UUID,
        animal_name: str,
        animal_species: str,
        submitted_at: datetime,
        decided_at: datetime | None,
        status: str,
        notes: str | None,
    ) -> None:
        self.id = id
        self.animal_id = animal_id
        self.animal_name = animal_name
        self.animal_species = animal_species
        self.submitted_at = submitted_at
        self.decided_at = decided_at
        self.status = status
        self.notes = notes


class ApplicationSummary:
    """Lightweight adoption application info for the dashboard."""

    __slots__ = ("animal_name", "animal_species", "id", "status", "submitted_at")

    def __init__(
        self,
        id: UUID,
        animal_name: str,
        animal_species: str,
        submitted_at: datetime,
        status: str,
    ) -> None:
        self.id = id
        self.animal_name = animal_name
        self.animal_species = animal_species
        self.submitted_at = submitted_at
        self.status = status


class DonationSummary:
    """Aggregated donation stats for the dashboard."""

    __slots__ = ("currency", "last_donation_at", "total_amount_cents", "total_count")

    def __init__(
        self,
        total_count: int,
        total_amount_cents: int,
        currency: str,
        last_donation_at: datetime | None,
    ) -> None:
        self.total_count = total_count
        self.total_amount_cents = total_amount_cents
        self.currency = currency
        self.last_donation_at = last_donation_at


class SponsoredAnimalSummary:
    """Sponsored animal info for the dashboard."""

    __slots__ = ("animal_id", "animal_name", "animal_species", "frequency", "status", "tier_name")

    def __init__(
        self,
        animal_id: UUID,
        animal_name: str,
        animal_species: str,
        tier_name: str,
        frequency: str,
        status: str,
    ) -> None:
        self.animal_id = animal_id
        self.animal_name = animal_name
        self.animal_species = animal_species
        self.tier_name = tier_name
        self.frequency = frequency
        self.status = status


class DashboardData:
    """Complete dashboard payload for a user."""

    __slots__ = (
        "applications",
        "display_name",
        "donation_summary",
        "email",
        "role",
        "sponsored_animals",
        "user_id",
    )

    def __init__(
        self,
        user_id: UUID,
        display_name: str,
        email: str,
        role: str,
        applications: list[ApplicationSummary],
        donation_summary: DonationSummary,
        sponsored_animals: list[SponsoredAnimalSummary],
    ) -> None:
        self.user_id = user_id
        self.display_name = display_name
        self.email = email
        self.role = role
        self.applications = applications
        self.donation_summary = donation_summary
        self.sponsored_animals = sponsored_animals


# -- Query helpers ------------------------------------------------------------


async def _get_applications(db: AsyncSession, user_email: str) -> list[ApplicationSummary]:
    """Fetch recent adoption applications for the user (matched by email)."""
    stmt = (
        select(
            AdoptionRequest.id,
            Animal.name,
            Animal.species,
            AdoptionRequest.submitted_at,
            AdoptionRequest.status,
        )
        .join(Adopter, AdoptionRequest.adopter_id == Adopter.id)
        .join(Animal, AdoptionRequest.animal_id == Animal.id)
        .where(Adopter.email == user_email, Adopter.deleted_at.is_(None))
        .order_by(AdoptionRequest.submitted_at.desc())
        .limit(MAX_APPLICATIONS)
    )
    result = await db.execute(stmt)
    return [
        ApplicationSummary(
            id=row.id,
            animal_name=row.name,
            animal_species=row.species,
            submitted_at=row.submitted_at,
            status=row.status,
        )
        for row in result.all()
    ]


async def _get_donation_summary(db: AsyncSession, user_email: str) -> DonationSummary:
    """Aggregate donation stats for the user (matched by email)."""
    stmt = (
        select(
            func.count(Donation.id).label("total_count"),
            func.coalesce(func.sum(Donation.amount_cents), 0).label("total_amount_cents"),
            func.max(Donation.created_at).label("last_donation_at"),
            Donor.currency_preference,
        )
        .join(Donor, Donation.donor_id == Donor.id)
        .where(
            Donor.email == user_email,
            Donation.status == DonationStatus.COMPLETED,
        )
        .group_by(Donor.currency_preference)
    )
    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        return DonationSummary(
            total_count=0,
            total_amount_cents=0,
            currency="EUR",
            last_donation_at=None,
        )

    return DonationSummary(
        total_count=row.total_count,
        total_amount_cents=row.total_amount_cents,
        currency=row.currency_preference,
        last_donation_at=row.last_donation_at,
    )


async def _get_sponsored_animals(db: AsyncSession, user_email: str) -> list[SponsoredAnimalSummary]:
    """Fetch sponsored animals for the user (matched by email via donors)."""
    stmt = (
        select(
            Animal.id.label("animal_id"),
            Animal.name.label("animal_name"),
            Animal.species.label("animal_species"),
            SponsorshipTier.name.label("tier_name"),
            Sponsorship.frequency,
            Sponsorship.status,
        )
        .join(Donor, Sponsorship.donor_id == Donor.id)
        .join(Animal, Sponsorship.animal_id == Animal.id)
        .join(SponsorshipTier, Sponsorship.tier_id == SponsorshipTier.id)
        .where(
            Donor.email == user_email,
            Sponsorship.status.in_([SponsorshipStatus.ACTIVE, SponsorshipStatus.PAUSED]),
        )
        .order_by(Sponsorship.started_at.desc())
        .limit(MAX_SPONSORED_ANIMALS)
    )
    result = await db.execute(stmt)
    return [
        SponsoredAnimalSummary(
            animal_id=row.animal_id,
            animal_name=row.animal_name,
            animal_species=row.animal_species,
            tier_name=row.tier_name,
            frequency=row.frequency,
            status=row.status,
        )
        for row in result.all()
    ]


# -- Query helpers (adopter-specific) -----------------------------------------


async def _get_application_details(db: AsyncSession, user_email: str) -> list[ApplicationDetail]:
    """Fetch all adoption applications with full detail for the adopter status page.

    Returns all applications (no limit) sorted by most recent first.
    Matches the user to their Adopter profile by email.
    """
    stmt = (
        select(
            AdoptionRequest.id,
            Animal.id.label("animal_id"),
            Animal.name,
            Animal.species,
            AdoptionRequest.submitted_at,
            AdoptionRequest.decided_at,
            AdoptionRequest.status,
            AdoptionRequest.notes,
        )
        .join(Adopter, AdoptionRequest.adopter_id == Adopter.id)
        .join(Animal, AdoptionRequest.animal_id == Animal.id)
        .where(Adopter.email == user_email, Adopter.deleted_at.is_(None))
        .order_by(AdoptionRequest.submitted_at.desc())
    )
    result = await db.execute(stmt)
    return [
        ApplicationDetail(
            id=row.id,
            animal_id=row.animal_id,
            animal_name=row.name,
            animal_species=row.species,
            submitted_at=row.submitted_at,
            decided_at=row.decided_at,
            status=row.status,
            notes=row.notes,
        )
        for row in result.all()
    ]


# -- Public API ---------------------------------------------------------------


async def get_adopter_applications(db: AsyncSession, user: User) -> list[ApplicationDetail]:
    """Return all adoption applications with full detail for the authenticated user.

    Matches the user to their Adopter record by email. Returns all applications
    (no pagination limit) since adopters rarely have more than a handful.
    """
    applications = await _get_application_details(db, user.email)
    logger.info(
        "Adopter applications loaded for user_id=%s: %d applications",
        user.id,
        len(applications),
    )
    return applications


async def get_dashboard_data(db: AsyncSession, user: User) -> DashboardData:
    """Build the complete dashboard payload for the authenticated user.

    Matches the user to adopter/donor profiles by email so that data
    from the legacy adopters/donors tables is included.
    """
    display_name = user.full_name or user.email.split("@")[0]

    applications = await _get_applications(db, user.email)
    donation_summary = await _get_donation_summary(db, user.email)
    sponsored_animals = await _get_sponsored_animals(db, user.email)

    logger.info(
        "Dashboard loaded for user_id=%s: %d applications, %d donations, %d sponsorships",
        user.id,
        len(applications),
        donation_summary.total_count,
        len(sponsored_animals),
    )

    return DashboardData(
        user_id=user.id,
        display_name=display_name,
        email=user.email,
        role=user.role,
        applications=applications,
        donation_summary=donation_summary,
        sponsored_animals=sponsored_animals,
    )
