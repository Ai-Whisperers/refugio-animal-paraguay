"""Service layer for annual financial report generation.

Aggregates income, expenses, donor metrics, animal outcomes,
and efficiency metrics for a given fiscal year. Outputs structured
data suitable for PDF and CSV export.

If a SQLAlchemy ``AsyncSession`` is provided to :func:`generate_annual_report`,
real database data is used.  Without a session the function returns a
zeroed-out placeholder report (backward-compatible behaviour).
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MonthlyBreakdown:
    """Revenue and expense totals for a single month."""

    month: int
    month_name: str
    income_cents: int = 0
    expenses_cents: int = 0

    @property
    def net_cents(self) -> int:
        return self.income_cents - self.expenses_cents


@dataclass
class CategoryBreakdown:
    """Expense total for a single category."""

    category: str
    amount_cents: int = 0
    percentage: float = 0.0


@dataclass
class CampaignSummary:
    """Top campaign summary."""

    campaign_name: str
    total_donations_cents: int = 0
    donor_count: int = 0


@dataclass
class DonorMetrics:
    """Donor statistics for the year."""

    total_donors: int = 0
    new_donors: int = 0
    recurring_donors: int = 0
    average_donation_cents: int = 0


@dataclass
class AnimalOutcomes:
    """Animal-related outcome counts for the year."""

    rescued: int = 0
    adopted: int = 0
    castrated: int = 0
    treated: int = 0


@dataclass
class FinancialEfficiency:
    """Efficiency metrics showing how donations are used."""

    direct_care_percentage: float = 0.0
    admin_percentage: float = 0.0
    direct_care_cents: int = 0
    admin_cents: int = 0


@dataclass
class AnnualReport:
    """Complete annual financial report data."""

    year: int
    generated_at: str = ""
    generated_by: str = ""

    # Executive summary
    total_income_cents: int = 0
    total_expenses_cents: int = 0

    # Breakdowns
    income_by_source: dict[str, int] = field(default_factory=dict)
    expense_categories: list[CategoryBreakdown] = field(default_factory=list)
    monthly_breakdown: list[MonthlyBreakdown] = field(default_factory=list)
    top_campaigns: list[CampaignSummary] = field(default_factory=list)

    # Metrics
    donor_metrics: DonorMetrics = field(default_factory=DonorMetrics)
    animal_outcomes: AnimalOutcomes = field(default_factory=AnimalOutcomes)
    efficiency: FinancialEfficiency = field(default_factory=FinancialEfficiency)

    @property
    def net_result_cents(self) -> int:
        return self.total_income_cents - self.total_expenses_cents

    @property
    def currency(self) -> str:
        return "PYG"


# ---------------------------------------------------------------------------
# Month names (Spanish)
# ---------------------------------------------------------------------------

MONTH_NAMES_ES = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def generate_annual_report(
    year: int,
    admin_name: str = "Administrador",
) -> AnnualReport:
    """Generate a zeroed-out annual report (backward-compatible placeholder).

    Use :func:`generate_annual_report_from_db` when a database session is
    available.

    Args:
        year: The fiscal year to report on.
        admin_name: Name of the admin generating the report.

    Returns:
        Complete AnnualReport dataclass with zero values.
    """
    report = AnnualReport(
        year=year,
        generated_at=datetime.now(tz=UTC).isoformat(),
        generated_by=admin_name,
    )

    report.total_income_cents = 0
    report.total_expenses_cents = 0
    report.income_by_source = {
        "campaigns": 0,
        "general": 0,
        "sponsorships": 0,
        "events": 0,
    }

    report.monthly_breakdown = [
        MonthlyBreakdown(month=m, month_name=MONTH_NAMES_ES[m]) for m in range(1, 13)
    ]

    categories = ["food", "medical", "transport", "housing", "other"]
    report.expense_categories = [
        CategoryBreakdown(category=c, amount_cents=0, percentage=0.0) for c in categories
    ]

    return report


async def generate_annual_report_from_db(
    db: AsyncSession,
    year: int,
    admin_name: str = "Administrador",
) -> AnnualReport:
    """Generate an annual financial report populated from the database.

    Queries Donation, FundAllocation, Donor, AdoptionRequest, and Animal
    tables for the given calendar year and populates all sections of the
    :class:`AnnualReport` dataclass.

    Args:
        db: Async SQLAlchemy session.
        year: Calendar year to report on (e.g. 2026).
        admin_name: Display name of the staff member generating the report.

    Returns:
        Fully populated AnnualReport.
    """
    from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
    from src.db.models.animal import Animal
    from src.db.models.donation import Donation, DonationStatus, Donor
    from src.db.models.fund_allocation import FundAllocation

    report = AnnualReport(
        year=year,
        generated_at=datetime.now(tz=UTC).isoformat(),
        generated_by=admin_name,
    )

    year_start = datetime(year, 1, 1, tzinfo=UTC)
    year_end = datetime(year + 1, 1, 1, tzinfo=UTC)

    # ------------------------------------------------------------------
    # Income: completed donations in the year
    # ------------------------------------------------------------------
    income_q = (
        select(
            Donation.target_type,
            func.sum(Donation.amount_cents).label("total_cents"),
        )
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.created_at >= year_start,
            Donation.created_at < year_end,
        )
        .group_by(Donation.target_type)
    )
    income_rows = (await db.execute(income_q)).all()

    income_by_source: dict[str, int] = {
        "campaigns": 0,
        "general": 0,
        "sponsorships": 0,
        "events": 0,
    }
    total_income = 0
    for row in income_rows:
        source = row.target_type if row.target_type in income_by_source else "general"
        income_by_source[source] = income_by_source.get(source, 0) + int(row.total_cents or 0)
        total_income += int(row.total_cents or 0)

    report.total_income_cents = total_income
    report.income_by_source = income_by_source

    # ------------------------------------------------------------------
    # Expenses: fund allocations in the year
    # ------------------------------------------------------------------
    expense_q = (
        select(
            FundAllocation.category,
            func.sum(FundAllocation.amount_cents).label("total_cents"),
        )
        .where(
            FundAllocation.transaction_date >= year_start,
            FundAllocation.transaction_date < year_end,
        )
        .group_by(FundAllocation.category)
        .order_by(func.sum(FundAllocation.amount_cents).desc())
    )
    expense_rows = (await db.execute(expense_q)).all()
    total_expenses = sum(int(r.total_cents or 0) for r in expense_rows)
    report.total_expenses_cents = total_expenses

    categories_seen: list[CategoryBreakdown] = []
    for row in expense_rows:
        pct = (
            round(int(row.total_cents or 0) / total_expenses * 100, 2)
            if total_expenses > 0
            else 0.0
        )
        categories_seen.append(
            CategoryBreakdown(
                category=row.category,
                amount_cents=int(row.total_cents or 0),
                percentage=pct,
            )
        )
    report.expense_categories = (
        categories_seen
        if categories_seen
        else [
            CategoryBreakdown(category=c, amount_cents=0, percentage=0.0)
            for c in ["food", "medical", "operations", "admin", "other"]
        ]
    )

    # ------------------------------------------------------------------
    # Monthly income + expenses breakdown
    # ------------------------------------------------------------------
    monthly_income_q = (
        select(
            extract("month", Donation.created_at).label("month"),
            func.sum(Donation.amount_cents).label("total_cents"),
        )
        .where(
            Donation.status == DonationStatus.COMPLETED,
            Donation.created_at >= year_start,
            Donation.created_at < year_end,
        )
        .group_by(extract("month", Donation.created_at))
    )
    monthly_income_rows = (await db.execute(monthly_income_q)).all()
    monthly_income: dict[int, int] = {
        int(r.month): int(r.total_cents or 0) for r in monthly_income_rows
    }

    monthly_expense_q = (
        select(
            extract("month", FundAllocation.transaction_date).label("month"),
            func.sum(FundAllocation.amount_cents).label("total_cents"),
        )
        .where(
            FundAllocation.transaction_date >= year_start,
            FundAllocation.transaction_date < year_end,
        )
        .group_by(extract("month", FundAllocation.transaction_date))
    )
    monthly_expense_rows = (await db.execute(monthly_expense_q)).all()
    monthly_expenses: dict[int, int] = {
        int(r.month): int(r.total_cents or 0) for r in monthly_expense_rows
    }

    report.monthly_breakdown = [
        MonthlyBreakdown(
            month=m,
            month_name=MONTH_NAMES_ES[m],
            income_cents=monthly_income.get(m, 0),
            expenses_cents=monthly_expenses.get(m, 0),
        )
        for m in range(1, 13)
    ]

    # ------------------------------------------------------------------
    # Donor metrics
    # ------------------------------------------------------------------
    total_donors_q = select(func.count(Donor.id.distinct())).where(
        Donor.created_at < year_end,
    )
    total_donors = int((await db.execute(total_donors_q)).scalar() or 0)

    new_donors_q = select(func.count(Donor.id)).where(
        Donor.created_at >= year_start,
        Donor.created_at < year_end,
    )
    new_donors = int((await db.execute(new_donors_q)).scalar() or 0)

    recurring_q = select(func.count(Donation.donor_id.distinct())).where(
        Donation.is_recurring.is_(True),
        Donation.status == DonationStatus.COMPLETED,
        Donation.created_at >= year_start,
        Donation.created_at < year_end,
        Donation.donor_id.is_not(None),
    )
    recurring_donors = int((await db.execute(recurring_q)).scalar() or 0)

    avg_donation_q = select(func.avg(Donation.amount_cents).label("avg")).where(
        Donation.status == DonationStatus.COMPLETED,
        Donation.created_at >= year_start,
        Donation.created_at < year_end,
    )
    avg_result = (await db.execute(avg_donation_q)).scalar()
    avg_donation_cents = int(avg_result) if avg_result is not None else 0

    report.donor_metrics = DonorMetrics(
        total_donors=total_donors,
        new_donors=new_donors,
        recurring_donors=recurring_donors,
        average_donation_cents=avg_donation_cents,
    )

    # ------------------------------------------------------------------
    # Animal outcomes
    # ------------------------------------------------------------------
    rescued_q = select(func.count(Animal.id)).where(
        Animal.created_at >= year_start,
        Animal.created_at < year_end,
    )
    rescued = int((await db.execute(rescued_q)).scalar() or 0)

    adopted_q = select(func.count(AdoptionRequest.id)).where(
        AdoptionRequest.status == AdoptionRequestStatus.APPROVED,
        AdoptionRequest.updated_at >= year_start,
        AdoptionRequest.updated_at < year_end,
    )
    adopted = int((await db.execute(adopted_q)).scalar() or 0)

    report.animal_outcomes = AnimalOutcomes(
        rescued=rescued,
        adopted=adopted,
        castrated=0,  # surgery data not queried in this iteration
        treated=0,
    )

    # ------------------------------------------------------------------
    # Financial efficiency
    # ------------------------------------------------------------------
    if total_income > 0:
        direct_care_cats = {"food", "medical", "operations"}
        direct_care = sum(
            c.amount_cents for c in report.expense_categories if c.category in direct_care_cats
        )
        admin_cats = {"admin", "administration", "fundraising"}
        admin_amount = sum(
            c.amount_cents for c in report.expense_categories if c.category in admin_cats
        )
        report.efficiency = FinancialEfficiency(
            direct_care_percentage=round(direct_care / total_income * 100, 1),
            admin_percentage=round(admin_amount / total_income * 100, 1),
            direct_care_cents=direct_care,
            admin_cents=admin_amount,
        )

    return report


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def export_summary_csv(report: AnnualReport) -> str:
    """Export the executive summary as CSV text."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Reporte Financiero Anual", str(report.year)])
    writer.writerow(["Generado", report.generated_at])
    writer.writerow(["Certificado por", report.generated_by])
    writer.writerow([])

    writer.writerow(["Resumen Ejecutivo"])
    writer.writerow(["Total Ingresos", report.total_income_cents])
    writer.writerow(["Total Gastos", report.total_expenses_cents])
    writer.writerow(["Resultado Neto", report.net_result_cents])
    writer.writerow([])

    writer.writerow(["Ingresos por Fuente"])
    for source, amount in report.income_by_source.items():
        writer.writerow([source, amount])
    writer.writerow([])

    writer.writerow(["Metricas de Donantes"])
    writer.writerow(["Total donantes", report.donor_metrics.total_donors])
    writer.writerow(["Nuevos donantes", report.donor_metrics.new_donors])
    writer.writerow(["Donantes recurrentes", report.donor_metrics.recurring_donors])
    writer.writerow(["Donacion promedio", report.donor_metrics.average_donation_cents])

    return output.getvalue()


def export_expenses_csv(report: AnnualReport) -> str:
    """Export expense breakdown as CSV text."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Categoria", "Monto", "Porcentaje"])
    for cat in report.expense_categories:
        writer.writerow([cat.category, cat.amount_cents, f"{cat.percentage:.1f}%"])

    return output.getvalue()


def export_monthly_csv(report: AnnualReport) -> str:
    """Export monthly breakdown as CSV text."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Mes", "Ingresos", "Gastos", "Neto"])
    for m in report.monthly_breakdown:
        writer.writerow([m.month_name, m.income_cents, m.expenses_cents, m.net_cents])

    return output.getvalue()


def export_campaigns_csv(report: AnnualReport) -> str:
    """Export top campaigns as CSV text."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Campana", "Total Donaciones", "Cantidad Donantes"])
    for c in report.top_campaigns:
        writer.writerow([c.campaign_name, c.total_donations_cents, c.donor_count])

    return output.getvalue()
