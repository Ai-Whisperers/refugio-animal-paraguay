"""EU tax compliance export service (RAP-257).

Generates bulk annual CSV exports of completed donations from EU-registered donors.
Intended for batch tax authority submission and internal compliance records.

The export covers all completed donations in a calendar year grouped by EU donor,
with per-currency subtotals and donation counts.

Design notes:
- EU membership is determined by Donor.country (ISO 3166-1 alpha-2 code).
- Only completed donations are included (DonationStatus.COMPLETED).
- Amount in the exported CSV is expressed in original currency cents, with a
  human-readable display column for convenience.
- Anonymous donations (donor_id IS NULL) are excluded — they cannot be attributed.
"""

from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.donation import Donation, DonationStatus, Donor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# EU member states — ISO 3166-1 alpha-2 codes (27 member states as of 2024)
# ---------------------------------------------------------------------------

EU_MEMBER_STATES: frozenset[str] = frozenset(
    {
        "AT",  # Austria
        "BE",  # Belgium
        "BG",  # Bulgaria
        "CY",  # Cyprus
        "CZ",  # Czech Republic
        "DE",  # Germany
        "DK",  # Denmark
        "EE",  # Estonia
        "ES",  # Spain
        "FI",  # Finland
        "FR",  # France
        "GR",  # Greece
        "HR",  # Croatia
        "HU",  # Hungary
        "IE",  # Ireland
        "IT",  # Italy
        "LT",  # Lithuania
        "LU",  # Luxembourg
        "LV",  # Latvia
        "MT",  # Malta
        "NL",  # Netherlands
        "PL",  # Poland
        "PT",  # Portugal
        "RO",  # Romania
        "SE",  # Sweden
        "SI",  # Slovenia
        "SK",  # Slovakia
    }
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EUDonorTaxRow:
    """Per-donor, per-currency aggregated donation totals for one year."""

    donor_id: str
    donor_name: str
    donor_email: str
    donor_country: str
    tax_id_type: str | None
    year: int
    currency: str
    donation_count: int
    total_amount_cents: int

    @property
    def total_amount_display(self) -> str:
        """Human-readable amount string."""
        if self.currency == "PYG":
            return f"{self.total_amount_cents:,} PYG"
        return f"{self.total_amount_cents / 100:,.2f} {self.currency}"


@dataclass(frozen=True)
class EUTaxExportResult:
    """Full EU tax compliance export for a given year."""

    generated_at: str
    year: int
    donor_count: int
    total_donations: int
    rows: list[EUDonorTaxRow]


# ---------------------------------------------------------------------------
# CSV column order
# ---------------------------------------------------------------------------

CSV_HEADERS = [
    "donor_id",
    "donor_name",
    "donor_email",
    "donor_country",
    "tax_id_type",
    "year",
    "currency",
    "donation_count",
    "total_amount_cents",
    "total_amount_display",
]

# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def get_eu_tax_export(
    db: AsyncSession,
    year: int,
) -> EUTaxExportResult:
    """Aggregate completed donations from EU donors for a given calendar year.

    Args:
        db: Async SQLAlchemy session.
        year: Calendar year (e.g. 2025).

    Returns:
        EUTaxExportResult with one row per (donor, currency) combination.
        Rows are sorted by donor_country, donor_name, currency.
    """
    eu_countries = sorted(EU_MEMBER_STATES)

    stmt = (
        select(
            Donor.id.label("donor_id"),
            Donor.full_name.label("donor_name"),
            Donor.email.label("donor_email"),
            Donor.country.label("donor_country"),
            Donor.tax_id_type.label("tax_id_type"),
            Donation.currency.label("currency"),
            func.count(Donation.id).label("donation_count"),
            func.sum(Donation.amount_cents).label("total_amount_cents"),
        )
        .join(Donation, Donation.donor_id == Donor.id)
        .where(
            Donor.country.in_(eu_countries),
            Donation.status == DonationStatus.COMPLETED,
            extract("year", Donation.created_at) == year,
        )
        .group_by(
            Donor.id,
            Donor.full_name,
            Donor.email,
            Donor.country,
            Donor.tax_id_type,
            Donation.currency,
        )
        .order_by(Donor.country, Donor.full_name, Donation.currency)
    )

    result = await db.execute(stmt)
    raw_rows = result.all()

    rows = [
        EUDonorTaxRow(
            donor_id=str(row.donor_id),
            donor_name=row.donor_name,
            donor_email=row.donor_email,
            donor_country=row.donor_country or "",
            tax_id_type=row.tax_id_type,
            year=year,
            currency=row.currency,
            donation_count=row.donation_count or 0,
            total_amount_cents=row.total_amount_cents or 0,
        )
        for row in raw_rows
    ]

    unique_donors = len({row.donor_id for row in rows})
    total_donations = sum(row.donation_count for row in rows)

    return EUTaxExportResult(
        generated_at=datetime.now(UTC).isoformat(),
        year=year,
        donor_count=unique_donors,
        total_donations=total_donations,
        rows=rows,
    )


def render_eu_tax_csv(result: EUTaxExportResult) -> bytes:
    """Serialise an EUTaxExportResult to UTF-8 encoded CSV bytes.

    Args:
        result: The export result from :func:`get_eu_tax_export`.

    Returns:
        UTF-8 encoded CSV bytes with header row + one data row per EUDonorTaxRow.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_HEADERS, lineterminator="\n")
    writer.writeheader()
    for row in result.rows:
        writer.writerow(
            {
                "donor_id": row.donor_id,
                "donor_name": row.donor_name,
                "donor_email": row.donor_email,
                "donor_country": row.donor_country,
                "tax_id_type": row.tax_id_type or "",
                "year": row.year,
                "currency": row.currency,
                "donation_count": row.donation_count,
                "total_amount_cents": row.total_amount_cents,
                "total_amount_display": row.total_amount_display,
            }
        )
    return buf.getvalue().encode("utf-8")
