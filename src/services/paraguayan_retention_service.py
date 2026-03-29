"""Paraguayan legal record retention policies for animal shelter operations.

Establishes required retention periods per Paraguayan law:
  - Ley 4840/2013 (Animal Welfare Law): mandates health records per animal
  - Ley 3140/2006 (Animal Disease Control): vaccination records must be maintained
  - Codigo Civil Paraguayo (Art. 633 ff.): civil contracts 10-year retention
  - Ley 125/91 (Tax Law): financial/donation records 5-year retention

These constants define the MINIMUM mandatory retention periods. The shelter
may retain records longer at its discretion.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_request import AdoptionRequest
from src.db.models.animal import Animal
from src.db.models.donation import Donation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retention period constants (in years)
# ---------------------------------------------------------------------------

# Adoption contract records — Codigo Civil Art. 633 (civil contracts)
ADOPTION_CONTRACT_RETENTION_YEARS: int = 10

# Animal health and veterinary records — Ley 4840/2013 (health records per animal)
ANIMAL_HEALTH_RECORD_RETENTION_YEARS: int = 5

# Vaccination records — Ley 3140/2006 (animal disease control)
VACCINATION_RECORD_RETENTION_YEARS: int = 5

# Donation and financial records — Ley 125/91 (Paraguayan tax law)
DONATION_RECORD_RETENTION_YEARS: int = 5

# Adopter personal data — retention after adoption relationship ends
ADOPTER_DATA_RETENTION_YEARS: int = 5

# General correspondence and contact submissions
CONTACT_RECORD_RETENTION_YEARS: int = 2


# ---------------------------------------------------------------------------
# Policy summary (structured for API response)
# ---------------------------------------------------------------------------

RETENTION_POLICY: list[dict] = [
    {
        "record_type": "adoption_contracts",
        "description": "Signed adoption contracts and related documents",
        "retention_years": ADOPTION_CONTRACT_RETENTION_YEARS,
        "legal_basis": "Codigo Civil Paraguayo, Art. 633 (civil contract obligations)",
        "trigger": "From the date of adoption or contract termination",
    },
    {
        "record_type": "animal_health_records",
        "description": "Animal health assessments, diagnoses, treatments, and shelter records",
        "retention_years": ANIMAL_HEALTH_RECORD_RETENTION_YEARS,
        "legal_basis": "Ley 4840/2013, Art. 12 (mandatory health records per animal)",
        "trigger": "From the date the animal leaves the shelter (adoption, death, or transfer)",
    },
    {
        "record_type": "vaccination_records",
        "description": "Rabies and other vaccination certificates per animal",
        "retention_years": VACCINATION_RECORD_RETENTION_YEARS,
        "legal_basis": "Ley 3140/2006, Art. 5 (rabies vaccination records mandatory)",
        "trigger": "From the date of the last vaccination administered",
    },
    {
        "record_type": "donation_records",
        "description": "Donation receipts, donor records, and financial transactions",
        "retention_years": DONATION_RECORD_RETENTION_YEARS,
        "legal_basis": "Ley 125/91, Art. 84 (Paraguayan tax law — financial record retention)",
        "trigger": "From the date of the donation transaction",
    },
    {
        "record_type": "adopter_personal_data",
        "description": "Adopter identification, address, contact information",
        "retention_years": ADOPTER_DATA_RETENTION_YEARS,
        "legal_basis": "Ley 4840/2013 + Codigo Civil Paraguayo (post-adoption follow-up obligations)",
        "trigger": "From the date the adoption relationship concludes (adoption or return)",
    },
    {
        "record_type": "contact_submissions",
        "description": "General enquiries and correspondence with the shelter",
        "retention_years": CONTACT_RECORD_RETENTION_YEARS,
        "legal_basis": "Shelter operational policy (no specific statutory requirement)",
        "trigger": "From the date of the submission",
    },
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class RetentionStatusResult:
    """Summary of record retention status check."""

    check_date: datetime = field(default_factory=lambda: datetime.now(UTC))
    pending_adoption_count: int = 0
    active_animal_count: int = 0
    recent_donation_count: int = 0
    oldest_adoption_date: datetime | None = None
    oldest_donation_date: datetime | None = None
    policy: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_retention_status(
    db: AsyncSession,
    *,
    now: datetime | None = None,
) -> RetentionStatusResult:
    """Check current record counts relevant to retention obligations.

    Returns a summary of active records that are subject to retention policies.
    This is informational — it does not delete any records.

    Args:
        db: Async SQLAlchemy session.
        now: Override for current time (testing only).

    Returns:
        RetentionStatusResult with counts and policy summary.
    """
    run_time = now or datetime.now(UTC)
    result = RetentionStatusResult(check_date=run_time, policy=RETENTION_POLICY)

    # Count animals still in shelter (active health records)
    animal_count_result = await db.execute(
        select(func.count()).where(Animal.status.not_in(["adopted", "deceased"]))
    )
    result.active_animal_count = animal_count_result.scalar_one()

    # Count pending/active adoptions
    adoption_count_result = await db.execute(
        select(func.count()).where(AdoptionRequest.status == "pending")
    )
    result.pending_adoption_count = adoption_count_result.scalar_one()

    # Count donations in the last 5 years (within retention window)
    donation_cutoff = run_time - timedelta(days=DONATION_RECORD_RETENTION_YEARS * 365)
    donation_count_result = await db.execute(
        select(func.count()).where(Donation.created_at >= donation_cutoff)
    )
    result.recent_donation_count = donation_count_result.scalar_one()

    logger.info(
        "Retention status check: %d active animals, %d pending adoptions, %d recent donations",
        result.active_animal_count,
        result.pending_adoption_count,
        result.recent_donation_count,
    )

    return result
