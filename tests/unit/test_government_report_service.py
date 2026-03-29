"""Unit tests for the Paraguayan government reporting service (RAP-248).

Tests cover:
- AnnualCensusReport dataclass defaults and to_dict()
- SpeciesBreakdown and StatusBreakdown dataclasses
- generate_annual_census: DB queries and report population
- render_annual_census_csv: CSV structure and content

API endpoint tests (auth, live DB) are in tests/integration/test_government_reporting.py.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.government_report_service import (
    REPORTING_AUTHORITY,
    SHELTER_LOCATION,
    SHELTER_NAME,
    AnnualCensusReport,
    SpeciesBreakdown,
    StatusBreakdown,
    generate_annual_census,
    render_annual_census_csv,
)

# ---------------------------------------------------------------------------
# AnnualCensusReport dataclass
# ---------------------------------------------------------------------------


class TestAnnualCensusReport:
    """Tests for AnnualCensusReport dataclass."""

    def test_defaults_are_zero(self) -> None:
        report = AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime.now(UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
        )
        assert report.total_intake == 0
        assert report.total_in_shelter == 0
        assert report.total_adopted == 0
        assert report.total_deceased == 0
        assert report.total_transferred == 0
        assert report.total_vaccinations_administered == 0

    def test_species_and_status_breakdowns_default_empty(self) -> None:
        report = AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime.now(UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
        )
        assert report.species_breakdown == []
        assert report.status_breakdown == []

    def test_to_dict_has_required_keys(self) -> None:
        report = AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime.now(UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
        )
        d = report.to_dict()
        required = {
            "reporting_year",
            "generated_at",
            "shelter_name",
            "shelter_location",
            "reporting_authority",
            "legal_basis",
            "summary",
            "species_breakdown",
            "status_breakdown",
        }
        assert required.issubset(d.keys())

    def test_to_dict_summary_has_all_counts(self) -> None:
        report = AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime.now(UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
            total_intake=10,
            total_adopted=5,
        )
        summary = report.to_dict()["summary"]
        assert summary["total_intake"] == 10
        assert summary["total_adopted"] == 5

    def test_to_dict_legal_basis_cites_ley_4840(self) -> None:
        report = AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime.now(UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
        )
        bases = " ".join(report.to_dict()["legal_basis"])
        assert "4840" in bases

    def test_to_dict_legal_basis_cites_ley_3140(self) -> None:
        report = AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime.now(UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
        )
        bases = " ".join(report.to_dict()["legal_basis"])
        assert "3140" in bases

    def test_to_dict_species_breakdown_serialised(self) -> None:
        report = AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime.now(UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
            species_breakdown=[
                SpeciesBreakdown(species="dog", species_label_es="Canino", count=15)
            ],
        )
        sb = report.to_dict()["species_breakdown"]
        assert len(sb) == 1
        assert sb[0]["species"] == "dog"
        assert sb[0]["species_label_es"] == "Canino"
        assert sb[0]["count"] == 15


# ---------------------------------------------------------------------------
# generate_annual_census service function
# ---------------------------------------------------------------------------


def _make_db_mock(*scalar_values: int) -> AsyncMock:
    """Return an AsyncMock db with scalar_one returning successive values."""
    side_effects = [MagicMock(scalar_one=MagicMock(return_value=v)) for v in scalar_values]
    # species and status breakdown queries return empty rows
    side_effects.append(MagicMock(all=MagicMock(return_value=[])))  # species
    side_effects.append(MagicMock(all=MagicMock(return_value=[])))  # status
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=side_effects)
    return db


class TestGenerateAnnualCensus:
    """Unit tests for generate_annual_census."""

    @pytest.mark.asyncio
    async def test_returns_annual_census_report(self) -> None:
        db = _make_db_mock(10, 5, 3, 1, 0, 20)
        result = await generate_annual_census(db, 2025)
        assert isinstance(result, AnnualCensusReport)

    @pytest.mark.asyncio
    async def test_total_intake_from_first_query(self) -> None:
        db = _make_db_mock(42, 0, 0, 0, 0, 0)
        result = await generate_annual_census(db, 2025)
        assert result.total_intake == 42

    @pytest.mark.asyncio
    async def test_total_in_shelter_from_second_query(self) -> None:
        db = _make_db_mock(0, 17, 0, 0, 0, 0)
        result = await generate_annual_census(db, 2025)
        assert result.total_in_shelter == 17

    @pytest.mark.asyncio
    async def test_total_adopted_from_third_query(self) -> None:
        db = _make_db_mock(0, 0, 8, 0, 0, 0)
        result = await generate_annual_census(db, 2025)
        assert result.total_adopted == 8

    @pytest.mark.asyncio
    async def test_total_vaccinations_from_sixth_query(self) -> None:
        db = _make_db_mock(0, 0, 0, 0, 0, 99)
        result = await generate_annual_census(db, 2025)
        assert result.total_vaccinations_administered == 99

    @pytest.mark.asyncio
    async def test_reporting_year_set_correctly(self) -> None:
        db = _make_db_mock(0, 0, 0, 0, 0, 0)
        result = await generate_annual_census(db, 2023)
        assert result.reporting_year == 2023

    @pytest.mark.asyncio
    async def test_now_override_sets_generated_at(self) -> None:
        fixed = datetime(2025, 6, 15, 10, 0, 0, tzinfo=UTC)
        db = _make_db_mock(0, 0, 0, 0, 0, 0)
        result = await generate_annual_census(db, 2025, now=fixed)
        assert result.generated_at == fixed

    @pytest.mark.asyncio
    async def test_shelter_name_set(self) -> None:
        db = _make_db_mock(0, 0, 0, 0, 0, 0)
        result = await generate_annual_census(db, 2025)
        assert result.shelter_name == SHELTER_NAME


# ---------------------------------------------------------------------------
# render_annual_census_csv
# ---------------------------------------------------------------------------


class TestRenderAnnualCensusCsv:
    """Unit tests for the CSV rendering function."""

    def _make_report(self) -> AnnualCensusReport:
        return AnnualCensusReport(
            reporting_year=2025,
            generated_at=datetime(2025, 12, 31, 23, 59, 0, tzinfo=UTC),
            shelter_name=SHELTER_NAME,
            shelter_location=SHELTER_LOCATION,
            reporting_authority=REPORTING_AUTHORITY,
            total_intake=50,
            total_adopted=30,
            species_breakdown=[
                SpeciesBreakdown(species="dog", species_label_es="Canino", count=40),
                SpeciesBreakdown(species="cat", species_label_es="Felino", count=10),
            ],
            status_breakdown=[
                StatusBreakdown(
                    status="available", status_label_es="Disponible para adopcion", count=20
                ),
                StatusBreakdown(status="adopted", status_label_es="Adoptado", count=30),
            ],
        )

    def test_returns_string(self) -> None:
        assert isinstance(render_annual_census_csv(self._make_report()), str)

    def test_starts_with_utf8_bom(self) -> None:
        csv_str = render_annual_census_csv(self._make_report())
        assert csv_str.startswith("\ufeff")

    def test_contains_senacsa_header(self) -> None:
        csv_str = render_annual_census_csv(self._make_report())
        assert "SENACSA" in csv_str

    def test_contains_reporting_year(self) -> None:
        csv_str = render_annual_census_csv(self._make_report())
        assert "2025" in csv_str

    def test_contains_intake_count(self) -> None:
        csv_str = render_annual_census_csv(self._make_report())
        assert "50" in csv_str

    def test_contains_adopted_count(self) -> None:
        csv_str = render_annual_census_csv(self._make_report())
        assert "30" in csv_str

    def test_contains_species_labels(self) -> None:
        csv_str = render_annual_census_csv(self._make_report())
        assert "Canino" in csv_str
        assert "Felino" in csv_str

    def test_contains_status_labels(self) -> None:
        csv_str = render_annual_census_csv(self._make_report())
        assert "Disponible para adopcion" in csv_str


# API endpoint tests (auth, live DB) are in tests/integration/test_government_reporting.py
