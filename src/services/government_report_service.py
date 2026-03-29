"""Paraguayan government reporting service (RAP-248).

Generates structured annual census reports for submission to SENACSA
(Servicio Nacional de Calidad y Salud Animal) and other Paraguayan
government agencies that oversee animal welfare.

Legal basis:
  - Ley 4840/2013, Art. 12: shelters must maintain and report animal records
  - Ley 3140/2006, Art. 5: vaccination records must be available to SENACSA
  - Resolucion SENACSA: annual census of registered animals required
"""

import csv
import io
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adoption_request import AdoptionRequest
from src.db.models.animal import Animal
from src.db.models.vaccination import Vaccination

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Report constants
# ---------------------------------------------------------------------------

SHELTER_NAME = "Refugio Animal Paraguay"
SHELTER_LOCATION = "Asuncion, Paraguay"
REPORTING_AUTHORITY = "SENACSA — Servicio Nacional de Calidad y Salud Animal"

# Species labels in Spanish (official government form language)
SPECIES_LABELS: dict[str, str] = {
    "dog": "Canino",
    "cat": "Felino",
    "rabbit": "Conejo",
    "bird": "Ave",
    "other": "Otro",
}

# Status labels in Spanish
STATUS_LABELS: dict[str, str] = {
    "intake": "Ingreso",
    "available": "Disponible para adopcion",
    "reserved": "Reservado",
    "adopted": "Adoptado",
    "fostered": "En acogida temporal",
    "medical_hold": "Retencion medica",
    "deceased": "Fallecido",
    "transferred": "Transferido",
}


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SpeciesBreakdown:
    """Count of animals by species for one reporting year."""

    species: str
    species_label_es: str
    count: int


@dataclass
class StatusBreakdown:
    """Count of animals by year-end status."""

    status: str
    status_label_es: str
    count: int


@dataclass
class AnnualCensusReport:
    """Full annual census report for a given calendar year."""

    reporting_year: int
    generated_at: datetime
    shelter_name: str
    shelter_location: str
    reporting_authority: str

    # Intake — animals first registered in this year
    total_intake: int = 0

    # Year-end inventory — animals present in shelter at 31 Dec
    total_in_shelter: int = 0

    # Outcomes during the year
    total_adopted: int = 0
    total_deceased: int = 0
    total_transferred: int = 0

    # Vaccinations administered during the year
    total_vaccinations_administered: int = 0
    total_rabies_vaccinations: int = 0

    # Breakdowns
    species_breakdown: list[SpeciesBreakdown] = field(default_factory=list)
    status_breakdown: list[StatusBreakdown] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return {
            "reporting_year": self.reporting_year,
            "generated_at": self.generated_at.isoformat(),
            "shelter_name": self.shelter_name,
            "shelter_location": self.shelter_location,
            "reporting_authority": self.reporting_authority,
            "legal_basis": [
                "Ley 4840/2013, Art. 12 (mandatory animal health records)",
                "Ley 3140/2006, Art. 5 (vaccination records — SENACSA)",
            ],
            "summary": {
                "total_intake": self.total_intake,
                "total_in_shelter": self.total_in_shelter,
                "total_adopted": self.total_adopted,
                "total_deceased": self.total_deceased,
                "total_transferred": self.total_transferred,
                "total_vaccinations_administered": self.total_vaccinations_administered,
                "total_rabies_vaccinations": self.total_rabies_vaccinations,
            },
            "species_breakdown": [
                {
                    "species": b.species,
                    "species_label_es": b.species_label_es,
                    "count": b.count,
                }
                for b in self.species_breakdown
            ],
            "status_breakdown": [
                {
                    "status": b.status,
                    "status_label_es": b.status_label_es,
                    "count": b.count,
                }
                for b in self.status_breakdown
            ],
        }


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def generate_annual_census(
    db: AsyncSession,
    year: int,
    *,
    now: datetime | None = None,
) -> AnnualCensusReport:
    """Generate an annual census report for the given calendar year.

    Queries the live database for all animals registered during the year,
    their vaccination records, and adoption outcomes.

    Args:
        db: Async SQLAlchemy session.
        year: Calendar year to report on (e.g. 2025).
        now: Override for current timestamp (testing only).

    Returns:
        AnnualCensusReport populated with counts from the database.
    """
    run_time = now or datetime.now(UTC)
    report = AnnualCensusReport(
        reporting_year=year,
        generated_at=run_time,
        shelter_name=SHELTER_NAME,
        shelter_location=SHELTER_LOCATION,
        reporting_authority=REPORTING_AUTHORITY,
    )

    # Animals first registered (intake) during the year
    intake_result = await db.execute(
        select(func.count()).where(extract("year", Animal.created_at) == year)
    )
    report.total_intake = intake_result.scalar_one()

    # Animals currently in-shelter (not adopted/deceased/transferred)
    in_shelter_result = await db.execute(
        select(func.count()).where(Animal.status.not_in(["adopted", "deceased", "transferred"]))
    )
    report.total_in_shelter = in_shelter_result.scalar_one()

    # Adoptions completed during the year — animals whose status became "adopted"
    # Use AdoptionRequest.updated_at as proxy for adoption date
    adopted_result = await db.execute(
        select(func.count()).where(
            AdoptionRequest.status == "approved",
            extract("year", AdoptionRequest.updated_at) == year,
        )
    )
    report.total_adopted = adopted_result.scalar_one()

    # Animals deceased during the year
    deceased_result = await db.execute(
        select(func.count()).where(
            Animal.status == "deceased",
            extract("year", Animal.updated_at) == year,
        )
    )
    report.total_deceased = deceased_result.scalar_one()

    # Animals transferred during the year
    transferred_result = await db.execute(
        select(func.count()).where(
            Animal.status == "transferred",
            extract("year", Animal.updated_at) == year,
        )
    )
    report.total_transferred = transferred_result.scalar_one()

    # Vaccinations administered during the year
    vacc_result = await db.execute(
        select(func.count()).where(
            Vaccination.vaccination_status == "administered",
            extract("year", Vaccination.administered_date) == year,
        )
    )
    report.total_vaccinations_administered = vacc_result.scalar_one()

    # Species breakdown — all animals ever registered
    species_rows = await db.execute(
        select(Animal.species, func.count().label("cnt")).group_by(Animal.species)
    )
    report.species_breakdown = [
        SpeciesBreakdown(
            species=row.species,
            species_label_es=SPECIES_LABELS.get(row.species) or row.species.capitalize(),
            count=row.cnt,
        )
        for row in species_rows.all()
    ]

    # Status breakdown — current status distribution
    status_rows = await db.execute(
        select(Animal.status, func.count().label("cnt")).group_by(Animal.status)
    )
    report.status_breakdown = [
        StatusBreakdown(
            status=row.status,
            status_label_es=STATUS_LABELS.get(row.status) or row.status.capitalize(),
            count=row.cnt,
        )
        for row in status_rows.all()
    ]

    logger.info(
        "Government census report generated: year=%d intake=%d adopted=%d vaccinations=%d",
        year,
        report.total_intake,
        report.total_adopted,
        report.total_vaccinations_administered,
    )

    return report


def render_annual_census_csv(report: AnnualCensusReport) -> str:
    """Render an AnnualCensusReport as a CSV string suitable for government submission.

    The CSV format follows the SENACSA annual shelter census template.
    Encoding: UTF-8 with BOM for compatibility with Microsoft Excel (Paraguay standard).

    Args:
        report: Populated AnnualCensusReport instance.

    Returns:
        CSV string (UTF-8 with BOM).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)

    # Header block
    writer.writerow(["INFORME ANUAL DE REFUGIO — SENACSA"])
    writer.writerow(["Refugio", report.shelter_name])
    writer.writerow(["Ubicacion", report.shelter_location])
    writer.writerow(["Ano de reporte", report.reporting_year])
    writer.writerow(["Generado", report.generated_at.strftime("%Y-%m-%d %H:%M UTC")])
    writer.writerow([])

    # Summary block
    writer.writerow(["RESUMEN ANUAL"])
    writer.writerow(["Indicador", "Valor"])
    writer.writerow(["Total ingresos en el ano", report.total_intake])
    writer.writerow(["Total animales en refugio (actual)", report.total_in_shelter])
    writer.writerow(["Total adopciones completadas", report.total_adopted])
    writer.writerow(["Total fallecidos", report.total_deceased])
    writer.writerow(["Total transferidos", report.total_transferred])
    writer.writerow(["Total vacunaciones administradas", report.total_vaccinations_administered])
    writer.writerow([])

    # Species breakdown
    writer.writerow(["DESGLOSE POR ESPECIE"])
    writer.writerow(["Especie (EN)", "Especie (ES)", "Cantidad"])
    for b in report.species_breakdown:
        writer.writerow([b.species, b.species_label_es, b.count])
    writer.writerow([])

    # Status breakdown
    writer.writerow(["DESGLOSE POR ESTADO ACTUAL"])
    writer.writerow(["Estado (EN)", "Estado (ES)", "Cantidad"])
    for b in report.status_breakdown:
        writer.writerow([b.status, b.status_label_es, b.count])

    # UTF-8 BOM for Excel compatibility
    return "\ufeff" + buf.getvalue()
