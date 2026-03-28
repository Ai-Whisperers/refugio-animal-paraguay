"""Service layer for annual financial report generation.

Aggregates income, expenses, donor metrics, animal outcomes,
and efficiency metrics for a given fiscal year. Outputs structured
data suitable for PDF and CSV export.
"""

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime

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
    """Generate a complete annual financial report for the given year.

    In production, this would query the database for actual data.
    For MVP, returns a structured report with placeholder/seed data.

    Args:
        year: The fiscal year to report on.
        admin_name: Name of the admin generating the report.

    Returns:
        Complete AnnualReport dataclass.
    """
    report = AnnualReport(
        year=year,
        generated_at=datetime.now().isoformat(),
        generated_by=admin_name,
    )

    # Placeholder data — in production, each section queries the DB
    report.total_income_cents = 0
    report.total_expenses_cents = 0
    report.income_by_source = {
        "campaigns": 0,
        "general": 0,
        "sponsorships": 0,
        "events": 0,
    }

    # Initialize 12 months
    report.monthly_breakdown = [
        MonthlyBreakdown(month=m, month_name=MONTH_NAMES_ES[m]) for m in range(1, 13)
    ]

    # Expense categories with 0%
    categories = ["food", "medical", "transport", "housing", "other"]
    report.expense_categories = [
        CategoryBreakdown(category=c, amount_cents=0, percentage=0.0) for c in categories
    ]

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
