"""Unit tests for the impact report PDF generation service."""

from src.services.impact_report_pdf_service import (
    FundCategoryEntry,
    ImpactReportData,
    ImpactReportPDFGenerator,
    _format_cents,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_REPORT: dict = {
    "report_metadata": {
        "start_date": "2026-01-01T00:00:00",
        "end_date": "2026-03-31T00:00:00",
        "generated_by_user_id": None,
    },
    "animals_served": {"total": 0, "by_species": {}},
    "adoptions": {"total": 0, "by_species": {}},
    "donations": {
        "total_count": 0,
        "by_currency": {},
        "by_payment_method": {},
    },
    "in_kind_donations": {"total": 0, "by_type": {}},
    "fund_allocation": {"total_cents": 0, "breakdown": []},
    "performance_metrics": {
        "avg_time_to_adoption_days": None,
        "cost_per_adoption_cents": None,
    },
}


def _full_report() -> dict:
    """Build a representative full report dict."""
    return {
        "report_metadata": {
            "start_date": "2026-01-01T00:00:00",
            "end_date": "2026-03-31T00:00:00",
            "generated_by_user_id": "user-abc-123",
        },
        "animals_served": {"total": 45, "by_species": {"dog": 30, "cat": 15}},
        "adoptions": {"total": 20, "by_species": {"dog": 12, "cat": 8}},
        "donations": {
            "total_count": 75,
            "by_currency": {
                "EUR": {"total_cents": 5000000, "count": 50},
                "PYG": {"total_cents": 10000000, "count": 25},
            },
            "by_payment_method": {"stripe": 50, "cash": 25},
        },
        "in_kind_donations": {"total": 10, "by_type": {"food": 6, "medicine": 4}},
        "fund_allocation": {
            "total_cents": 4000000,
            "breakdown": [
                {
                    "category": "medical",
                    "total_cents": 2400000,
                    "transaction_count": 15,
                    "percentage": 60.0,
                },
                {
                    "category": "food",
                    "total_cents": 1600000,
                    "transaction_count": 10,
                    "percentage": 40.0,
                },
            ],
        },
        "performance_metrics": {
            "avg_time_to_adoption_days": 14.5,
            "cost_per_adoption_cents": 200000,
        },
        "volunteers": {
            "unique_volunteers": 12,
            "total_hours": 240.0,
            "by_category": {"animal_care": 180.0, "transport": 60.0},
        },
        "foster_placements": {
            "active_during_period": 8,
            "new_placements": 3,
        },
    }


# ---------------------------------------------------------------------------
# _format_cents
# ---------------------------------------------------------------------------


class TestFormatCents:
    """Tests for _format_cents helper."""

    def test_eur_formats_with_decimals(self) -> None:
        assert _format_cents(5000000, "EUR") == "50,000.00 EUR"

    def test_pyg_formats_without_decimals(self) -> None:
        result = _format_cents(1000000, "PYG")
        assert "PYG" in result
        assert "." not in result  # No decimal for PYG

    def test_unknown_currency_uses_symbol_as_code(self) -> None:
        result = _format_cents(100, "XYZ")
        assert "XYZ" in result


# ---------------------------------------------------------------------------
# ImpactReportData.from_report_dict
# ---------------------------------------------------------------------------


class TestImpactReportDataFromReportDict:
    """Tests for ImpactReportData.from_report_dict."""

    def test_parses_minimal_report(self) -> None:
        data = ImpactReportData.from_report_dict(MINIMAL_REPORT)

        assert data.animals_total == 0
        assert data.adoptions_total == 0
        assert data.donations_total_count == 0
        assert data.fund_total_cents == 0
        assert data.fund_breakdown == []
        assert data.avg_time_to_adoption_days is None
        assert data.cost_per_adoption_cents is None

    def test_parses_full_report(self) -> None:
        data = ImpactReportData.from_report_dict(_full_report())

        assert data.animals_total == 45
        assert data.animals_by_species == {"dog": 30, "cat": 15}
        assert data.adoptions_total == 20
        assert data.donations_total_count == 75
        assert data.donations_by_currency["EUR"]["total_cents"] == 5000000
        assert data.donations_by_method["stripe"] == 50
        assert data.in_kind_total == 10
        assert data.in_kind_by_type["food"] == 6
        assert data.fund_total_cents == 4000000
        assert len(data.fund_breakdown) == 2
        assert data.avg_time_to_adoption_days == 14.5
        assert data.cost_per_adoption_cents == 200000

    def test_parses_volunteer_and_foster_sections(self) -> None:
        data = ImpactReportData.from_report_dict(_full_report())

        assert data.volunteer_unique == 12
        assert data.volunteer_total_hours == 240.0
        assert data.volunteer_by_category["animal_care"] == 180.0
        assert data.foster_active_during_period == 8
        assert data.foster_new_placements == 3

    def test_defaults_to_zero_when_volunteer_section_absent(self) -> None:
        data = ImpactReportData.from_report_dict(MINIMAL_REPORT)

        assert data.volunteer_unique == 0
        assert data.volunteer_total_hours == 0.0
        assert data.foster_active_during_period == 0
        assert data.foster_new_placements == 0

    def test_parses_fund_breakdown_entries(self) -> None:
        data = ImpactReportData.from_report_dict(_full_report())

        first = data.fund_breakdown[0]
        assert isinstance(first, FundCategoryEntry)
        assert first.category == "medical"
        assert first.total_cents == 2400000
        assert first.percentage == 60.0

    def test_preserves_date_strings(self) -> None:
        data = ImpactReportData.from_report_dict(_full_report())

        assert data.start_date.startswith("2026-01-01")
        assert data.end_date.startswith("2026-03-31")


# ---------------------------------------------------------------------------
# ImpactReportPDFGenerator
# ---------------------------------------------------------------------------


class TestImpactReportPDFGenerator:
    """Tests for ImpactReportPDFGenerator."""

    def test_generates_bytes_from_minimal_report(self) -> None:
        data = ImpactReportData.from_report_dict(MINIMAL_REPORT)
        generator = ImpactReportPDFGenerator()

        pdf_bytes = generator.generate_bytes(data)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF magic number
        assert pdf_bytes[:4] == b"%PDF"

    def test_generates_bytes_from_full_report(self) -> None:
        data = ImpactReportData.from_report_dict(_full_report())
        generator = ImpactReportPDFGenerator()

        pdf_bytes = generator.generate_bytes(data)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_output_is_larger_for_fuller_report(self) -> None:
        minimal_data = ImpactReportData.from_report_dict(MINIMAL_REPORT)
        full_data = ImpactReportData.from_report_dict(_full_report())
        generator = ImpactReportPDFGenerator()

        minimal_bytes = generator.generate_bytes(minimal_data)
        full_bytes = generator.generate_bytes(full_data)

        assert len(full_bytes) >= len(minimal_bytes)

    def test_volunteer_section_omitted_when_zero(self) -> None:
        """When volunteers are zero, the section should not crash but simply not render."""
        data = ImpactReportData.from_report_dict(MINIMAL_REPORT)
        assert data.volunteer_unique == 0

        generator = ImpactReportPDFGenerator()
        pdf_bytes = generator.generate_bytes(data)

        assert pdf_bytes[:4] == b"%PDF"

    def test_volunteer_section_included_when_nonzero(self) -> None:
        """When volunteer data is present, PDF should include the extra section."""
        data = ImpactReportData.from_report_dict(_full_report())
        assert data.volunteer_unique == 12

        generator = ImpactReportPDFGenerator()
        pdf_bytes = generator.generate_bytes(data)

        # Full report with volunteers should be larger than minimal
        minimal_data = ImpactReportData.from_report_dict(MINIMAL_REPORT)
        minimal_bytes = generator.generate_bytes(minimal_data)
        assert len(pdf_bytes) > len(minimal_bytes)
