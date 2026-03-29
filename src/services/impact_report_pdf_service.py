"""Impact report PDF generation service.

Generates a branded, multi-section impact report PDF suitable for donors,
board members, and government bodies. Renders all aggregated shelter metrics
returned by :func:`~src.services.impact_report_service.generate_impact_report`
into a structured printable document.

Uses the centralized :class:`~src.services.pdf_service.BasePDFGenerator` and
:class:`~src.services.pdf_service.ShelterPDF` for consistent shelter branding.

Usage::

    from src.services.impact_report_pdf_service import ImpactReportData, ImpactReportPDFGenerator

    data = ImpactReportData.from_report_dict(report_dict)
    generator = ImpactReportPDFGenerator()
    pdf_bytes = generator.generate_bytes(data)
"""

import logging
from dataclasses import dataclass, field

from src.services.pdf_service import BasePDFGenerator, ShelterPDF

logger = logging.getLogger(__name__)

# Report title shown in the ShelterPDF header
REPORT_TITLE = "INFORME DE IMPACTO / IMPACT REPORT"

CURRENCY_SYMBOLS: dict[str, str] = {
    "EUR": "EUR",
    "USD": "USD",
    "PYG": "PYG",
}

PAYMENT_METHOD_LABELS: dict[str, str] = {
    "stripe": "Tarjeta (Stripe)",
    "cash": "Efectivo",
    "transfer": "Transferencia bancaria",
    "sepa_debit": "Debito SEPA",
    "tigo_money": "Tigo Money",
    "other": "Otro",
}

SPECIES_LABELS: dict[str, str] = {
    "dog": "Perro",
    "cat": "Gato",
    "other": "Otro",
}


def _format_cents(amount_cents: int, currency: str) -> str:
    """Format amount in cents as a human-readable string."""
    if currency == "PYG":
        return f"{amount_cents:,} PYG"
    return f"{amount_cents / 100:,.2f} {CURRENCY_SYMBOLS.get(currency, currency)}"


@dataclass
class FundCategoryEntry:
    """Single fund allocation category line."""

    category: str
    total_cents: int
    transaction_count: int
    percentage: float


@dataclass
class ImpactReportData:
    """All data required to render an impact report PDF.

    Build via :meth:`from_report_dict` using the dict returned by
    :func:`~src.services.impact_report_service.generate_impact_report`.
    """

    # Metadata
    start_date: str
    end_date: str
    generated_by_user_id: str | None

    # Animals
    animals_total: int
    animals_by_species: dict[str, int]

    # Adoptions
    adoptions_total: int
    adoptions_by_species: dict[str, int]

    # Donations
    donations_total_count: int
    donations_by_currency: dict[str, dict]  # {currency: {total_cents, count}}
    donations_by_method: dict[str, int]

    # In-kind
    in_kind_total: int
    in_kind_by_type: dict[str, int]

    # Fund allocation
    fund_total_cents: int
    fund_breakdown: list[FundCategoryEntry]

    # Performance metrics
    avg_time_to_adoption_days: float | None
    cost_per_adoption_cents: int | None

    # Optional — may be absent if RAP-265 is not yet merged
    volunteer_unique: int = 0
    volunteer_total_hours: float = 0.0
    volunteer_by_category: dict[str, float] = field(default_factory=dict)
    foster_active_during_period: int = 0
    foster_new_placements: int = 0

    @classmethod
    def from_report_dict(cls, report: dict) -> "ImpactReportData":
        """Construct an ImpactReportData from a generate_impact_report() dict."""
        metadata = report.get("report_metadata", {})
        animals = report.get("animals_served", {})
        adoptions = report.get("adoptions", {})
        donations = report.get("donations", {})
        in_kind = report.get("in_kind_donations", {})
        fund = report.get("fund_allocation", {})
        perf = report.get("performance_metrics", {})

        raw_breakdown = fund.get("breakdown", [])
        breakdown = [
            FundCategoryEntry(
                category=item.get("category", ""),
                total_cents=int(item.get("total_cents", 0)),
                transaction_count=int(item.get("transaction_count", 0)),
                percentage=float(item.get("percentage", 0.0)),
            )
            for item in raw_breakdown
        ]

        # Optional volunteer / foster sections (added by RAP-265)
        volunteers = report.get("volunteers", {})
        foster = report.get("foster_placements", {})

        return cls(
            start_date=metadata.get("start_date", ""),
            end_date=metadata.get("end_date", ""),
            generated_by_user_id=metadata.get("generated_by_user_id"),
            animals_total=int(animals.get("total", 0)),
            animals_by_species=dict(animals.get("by_species", {})),
            adoptions_total=int(adoptions.get("total", 0)),
            adoptions_by_species=dict(adoptions.get("by_species", {})),
            donations_total_count=int(donations.get("total_count", 0)),
            donations_by_currency=dict(donations.get("by_currency", {})),
            donations_by_method=dict(donations.get("by_payment_method", {})),
            in_kind_total=int(in_kind.get("total", 0)),
            in_kind_by_type=dict(in_kind.get("by_type", {})),
            fund_total_cents=int(fund.get("total_cents", 0)),
            fund_breakdown=breakdown,
            avg_time_to_adoption_days=perf.get("avg_time_to_adoption_days"),
            cost_per_adoption_cents=perf.get("cost_per_adoption_cents"),
            volunteer_unique=int(volunteers.get("unique_volunteers", 0)),
            volunteer_total_hours=float(volunteers.get("total_hours", 0.0)),
            volunteer_by_category=dict(volunteers.get("by_category", {})),
            foster_active_during_period=int(foster.get("active_during_period", 0)),
            foster_new_placements=int(foster.get("new_placements", 0)),
        )


class ImpactReportPDFGenerator(BasePDFGenerator):
    """Generates branded impact report PDFs for Refugio Animal Paraguay.

    Example::

        data = ImpactReportData.from_report_dict(report_dict)
        generator = ImpactReportPDFGenerator()
        pdf_bytes = generator.generate_bytes(data)
    """

    def _build_pdf(self, data: ImpactReportData) -> ShelterPDF:  # type: ignore[override]
        """Build and return the populated impact report PDF."""
        pdf = ShelterPDF(title=REPORT_TITLE)
        pdf.add_page()

        self._render_date_range(pdf, data)
        self._render_animals_section(pdf, data)
        self._render_adoptions_section(pdf, data)
        self._render_donations_section(pdf, data)
        self._render_in_kind_section(pdf, data)
        self._render_fund_allocation_section(pdf, data)
        self._render_performance_section(pdf, data)

        if data.volunteer_unique > 0 or data.volunteer_total_hours > 0:
            self._render_volunteers_section(pdf, data)

        if data.foster_active_during_period > 0 or data.foster_new_placements > 0:
            self._render_foster_section(pdf, data)

        return pdf

    # ------------------------------------------------------------------
    # Section renderers
    # ------------------------------------------------------------------

    def _render_date_range(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render the report date range header."""
        pdf.set_font("Helvetica", "", 10)
        period_str = f"Periodo: {data.start_date[:10]}  -  {data.end_date[:10]}"
        pdf.cell(0, 6, period_str, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(4)

    def _render_animals_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render animals served section."""
        pdf.section_title("Animales Atendidos / Animals Served")
        pdf.info_row("Total animales:", str(data.animals_total))
        if data.animals_by_species:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Por especie:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for species, count in data.animals_by_species.items():
                label = SPECIES_LABELS.get(species, species.capitalize())
                pdf.info_row(f"  {label}:", str(count))
        pdf.ln(4)

    def _render_adoptions_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render adoptions section."""
        pdf.section_title("Adopciones / Adoptions")
        pdf.info_row("Total adoptiones:", str(data.adoptions_total))
        if data.adoptions_by_species:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Por especie:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for species, count in data.adoptions_by_species.items():
                label = SPECIES_LABELS.get(species, species.capitalize())
                pdf.info_row(f"  {label}:", str(count))
        pdf.ln(4)

    def _render_donations_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render monetary donations section."""
        pdf.section_title("Donaciones Monetarias / Monetary Donations")
        pdf.info_row("Total donaciones:", str(data.donations_total_count))

        if data.donations_by_currency:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Por moneda:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for currency, detail in data.donations_by_currency.items():
                total_cents = int(detail.get("total_cents", 0))
                count = int(detail.get("count", 0))
                amount_str = _format_cents(total_cents, currency)
                pdf.info_row(f"  {currency}:", f"{amount_str}  ({count} donaciones)")

        if data.donations_by_method:
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Por metodo de pago:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for method, count in data.donations_by_method.items():
                label = PAYMENT_METHOD_LABELS.get(method, method)
                pdf.info_row(f"  {label}:", str(count))
        pdf.ln(4)

    def _render_in_kind_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render in-kind donations section."""
        pdf.section_title("Donaciones en Especie / In-Kind Donations")
        pdf.info_row("Total donaciones en especie:", str(data.in_kind_total))
        if data.in_kind_by_type:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Por tipo:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for item_type, count in data.in_kind_by_type.items():
                pdf.info_row(f"  {item_type.capitalize()}:", str(count))
        pdf.ln(4)

    def _render_fund_allocation_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render fund allocation breakdown section."""
        pdf.section_title("Asignacion de Fondos / Fund Allocation")
        total_str = _format_cents(data.fund_total_cents, "EUR")
        pdf.info_row("Total asignado:", total_str)

        if data.fund_breakdown:
            pdf.ln(2)
            # Table header
            pdf.set_font("Helvetica", "B", 9)
            col_w = (pdf.w - pdf.l_margin - pdf.r_margin) / 3
            pdf.cell(col_w, 6, "Categoria", border="B")
            pdf.cell(col_w, 6, "Monto", border="B", align="R")
            pdf.cell(col_w, 6, "%", border="B", align="R", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 9)
            for entry in data.fund_breakdown:
                amount_str = _format_cents(entry.total_cents, "EUR")
                pdf.cell(col_w, 6, entry.category.capitalize())
                pdf.cell(col_w, 6, amount_str, align="R")
                pdf.cell(
                    col_w,
                    6,
                    f"{entry.percentage:.1f}%",
                    align="R",
                    new_x="LMARGIN",
                    new_y="NEXT",
                )
        pdf.ln(4)

    def _render_performance_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render performance KPIs section."""
        pdf.section_title("Indicadores de Rendimiento / Performance KPIs")

        if data.avg_time_to_adoption_days is not None:
            pdf.info_row(
                "Tiempo promedio hasta adopcion:",
                f"{data.avg_time_to_adoption_days:.1f} dias",
            )
        else:
            pdf.info_row("Tiempo promedio hasta adopcion:", "N/D")

        if data.cost_per_adoption_cents is not None:
            cost_str = _format_cents(data.cost_per_adoption_cents, "EUR")
            pdf.info_row("Costo por adopcion (estimado):", cost_str)
        else:
            pdf.info_row("Costo por adopcion (estimado):", "N/D")
        pdf.ln(4)

    def _render_volunteers_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render volunteer contributions section."""
        pdf.section_title("Voluntarios / Volunteers")
        pdf.info_row("Voluntarios activos:", str(data.volunteer_unique))
        pdf.info_row("Total horas voluntariado:", f"{data.volunteer_total_hours:.1f} h")
        if data.volunteer_by_category:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, "Por categoria:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            for category, hours in data.volunteer_by_category.items():
                pdf.info_row(f"  {category.replace('_', ' ').capitalize()}:", f"{hours:.1f} h")
        pdf.ln(4)

    def _render_foster_section(self, pdf: ShelterPDF, data: ImpactReportData) -> None:
        """Render foster placement section."""
        pdf.section_title("Hogares de Acogida / Foster Placements")
        pdf.info_row("Activos durante el periodo:", str(data.foster_active_during_period))
        pdf.info_row("Nuevas acogidas:", str(data.foster_new_placements))
        pdf.ln(4)
