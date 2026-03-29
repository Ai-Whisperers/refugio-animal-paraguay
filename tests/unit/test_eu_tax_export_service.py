"""Unit tests for eu_tax_export_service (RAP-257)."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.eu_tax_export_service import (
    CSV_HEADERS,
    EU_MEMBER_STATES,
    EUDonorTaxRow,
    EUTaxExportResult,
    get_eu_tax_export,
    render_eu_tax_csv,
)

# ---------------------------------------------------------------------------
# EU_MEMBER_STATES constant
# ---------------------------------------------------------------------------


def test_eu_member_states_contains_27_members() -> None:
    assert len(EU_MEMBER_STATES) == 27


def test_eu_member_states_contains_netherlands() -> None:
    assert "NL" in EU_MEMBER_STATES


def test_eu_member_states_excludes_non_eu() -> None:
    # UK left EU; Switzerland, USA, Paraguay never in EU
    for code in ("GB", "CH", "US", "PY", "NO"):
        assert code not in EU_MEMBER_STATES


def test_eu_member_states_is_frozenset() -> None:
    assert isinstance(EU_MEMBER_STATES, frozenset)


# ---------------------------------------------------------------------------
# EUDonorTaxRow.total_amount_display
# ---------------------------------------------------------------------------


def test_total_amount_display_eur() -> None:
    row = EUDonorTaxRow(
        donor_id=str(uuid4()),
        donor_name="Test Donor",
        donor_email="donor@example.com",
        donor_country="NL",
        tax_id_type="BSN",
        year=2025,
        currency="EUR",
        donation_count=3,
        total_amount_cents=15000,  # €150.00
    )
    assert row.total_amount_display == "150.00 EUR"


def test_total_amount_display_pyg() -> None:
    row = EUDonorTaxRow(
        donor_id=str(uuid4()),
        donor_name="Test Donor",
        donor_email="donor@example.com",
        donor_country="DE",
        tax_id_type=None,
        year=2025,
        currency="PYG",
        donation_count=1,
        total_amount_cents=500000,
    )
    assert row.total_amount_display == "500,000 PYG"


def test_total_amount_display_usd() -> None:
    row = EUDonorTaxRow(
        donor_id=str(uuid4()),
        donor_name="Test Donor",
        donor_email="donor@example.com",
        donor_country="FR",
        tax_id_type=None,
        year=2025,
        currency="USD",
        donation_count=2,
        total_amount_cents=5000,  # $50.00
    )
    assert row.total_amount_display == "50.00 USD"


# ---------------------------------------------------------------------------
# render_eu_tax_csv
# ---------------------------------------------------------------------------


def _make_export(rows: list[EUDonorTaxRow], year: int = 2025) -> EUTaxExportResult:
    unique_donors = len({r.donor_id for r in rows})
    total = sum(r.donation_count for r in rows)
    return EUTaxExportResult(
        generated_at=datetime.now(UTC).isoformat(),
        year=year,
        donor_count=unique_donors,
        total_donations=total,
        rows=rows,
    )


def test_render_csv_headers() -> None:
    export = _make_export([])
    csv_bytes = render_eu_tax_csv(export)
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    assert reader.fieldnames == CSV_HEADERS


def test_render_csv_empty_rows_only_header() -> None:
    export = _make_export([])
    csv_bytes = render_eu_tax_csv(export)
    lines = csv_bytes.decode("utf-8").strip().splitlines()
    assert len(lines) == 1  # header only


def test_render_csv_single_row() -> None:
    donor_id = str(uuid4())
    row = EUDonorTaxRow(
        donor_id=donor_id,
        donor_name="Jan Janssen",
        donor_email="jan@example.nl",
        donor_country="NL",
        tax_id_type="BSN",
        year=2025,
        currency="EUR",
        donation_count=4,
        total_amount_cents=20000,
    )
    export = _make_export([row])
    csv_bytes = render_eu_tax_csv(export)
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    data_rows = list(reader)
    assert len(data_rows) == 1
    r = data_rows[0]
    assert r["donor_id"] == donor_id
    assert r["donor_name"] == "Jan Janssen"
    assert r["donor_email"] == "jan@example.nl"
    assert r["donor_country"] == "NL"
    assert r["tax_id_type"] == "BSN"
    assert r["year"] == "2025"
    assert r["currency"] == "EUR"
    assert r["donation_count"] == "4"
    assert r["total_amount_cents"] == "20000"
    assert r["total_amount_display"] == "200.00 EUR"


def test_render_csv_null_tax_id_type_renders_empty_string() -> None:
    row = EUDonorTaxRow(
        donor_id=str(uuid4()),
        donor_name="Maria Schmidt",
        donor_email="maria@example.de",
        donor_country="DE",
        tax_id_type=None,
        year=2025,
        currency="EUR",
        donation_count=1,
        total_amount_cents=5000,
    )
    export = _make_export([row])
    csv_bytes = render_eu_tax_csv(export)
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    data_rows = list(reader)
    assert data_rows[0]["tax_id_type"] == ""


def test_render_csv_multiple_rows() -> None:
    rows = [
        EUDonorTaxRow(
            donor_id=str(uuid4()),
            donor_name=f"Donor {i}",
            donor_email=f"donor{i}@example.com",
            donor_country="NL",
            tax_id_type=None,
            year=2025,
            currency="EUR",
            donation_count=i,
            total_amount_cents=i * 1000,
        )
        for i in range(1, 6)
    ]
    export = _make_export(rows)
    csv_bytes = render_eu_tax_csv(export)
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    data_rows = list(reader)
    assert len(data_rows) == 5


def test_render_csv_is_utf8_bytes() -> None:
    row = EUDonorTaxRow(
        donor_id=str(uuid4()),
        donor_name="André García",  # accented characters
        donor_email="andre@example.es",
        donor_country="ES",
        tax_id_type="TIN",
        year=2025,
        currency="EUR",
        donation_count=1,
        total_amount_cents=10000,
    )
    export = _make_export([row])
    csv_bytes = render_eu_tax_csv(export)
    assert isinstance(csv_bytes, bytes)
    # Should decode without error
    decoded = csv_bytes.decode("utf-8")
    assert "André García" in decoded


# ---------------------------------------------------------------------------
# get_eu_tax_export — async service with mocked DB
# ---------------------------------------------------------------------------


def _make_db_row(**kwargs: Any) -> MagicMock:
    """Build a mock SQLAlchemy row with given attributes."""
    row = MagicMock()
    for key, value in kwargs.items():
        setattr(row, key, value)
    return row


@pytest.mark.asyncio
async def test_get_eu_tax_export_empty_result() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    db.execute.return_value = mock_result

    result = await get_eu_tax_export(db, year=2025)

    assert result.year == 2025
    assert result.donor_count == 0
    assert result.total_donations == 0
    assert result.rows == []


@pytest.mark.asyncio
async def test_get_eu_tax_export_single_donor_single_currency() -> None:
    db = AsyncMock()
    donor_id = uuid4()
    raw_row = _make_db_row(
        donor_id=donor_id,
        donor_name="Jan Janssen",
        donor_email="jan@example.nl",
        donor_country="NL",
        tax_id_type="BSN",
        currency="EUR",
        donation_count=3,
        total_amount_cents=30000,
    )
    mock_result = MagicMock()
    mock_result.all.return_value = [raw_row]
    db.execute.return_value = mock_result

    result = await get_eu_tax_export(db, year=2025)

    assert result.year == 2025
    assert result.donor_count == 1
    assert result.total_donations == 3
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.donor_id == str(donor_id)
    assert row.donor_name == "Jan Janssen"
    assert row.donor_country == "NL"
    assert row.currency == "EUR"
    assert row.donation_count == 3
    assert row.total_amount_cents == 30000


@pytest.mark.asyncio
async def test_get_eu_tax_export_multiple_donors_multiple_currencies() -> None:
    db = AsyncMock()
    donor_a = uuid4()
    donor_b = uuid4()
    raw_rows = [
        _make_db_row(
            donor_id=donor_a,
            donor_name="Donor A",
            donor_email="a@example.de",
            donor_country="DE",
            tax_id_type=None,
            currency="EUR",
            donation_count=2,
            total_amount_cents=10000,
        ),
        _make_db_row(
            donor_id=donor_a,
            donor_name="Donor A",
            donor_email="a@example.de",
            donor_country="DE",
            tax_id_type=None,
            currency="USD",
            donation_count=1,
            total_amount_cents=5000,
        ),
        _make_db_row(
            donor_id=donor_b,
            donor_name="Donor B",
            donor_email="b@example.fr",
            donor_country="FR",
            tax_id_type="TIN",
            currency="EUR",
            donation_count=5,
            total_amount_cents=50000,
        ),
    ]
    mock_result = MagicMock()
    mock_result.all.return_value = raw_rows
    db.execute.return_value = mock_result

    result = await get_eu_tax_export(db, year=2024)

    assert result.year == 2024
    assert result.donor_count == 2
    assert result.total_donations == 8
    assert len(result.rows) == 3


@pytest.mark.asyncio
async def test_get_eu_tax_export_null_amounts_default_to_zero() -> None:
    db = AsyncMock()
    donor_id = uuid4()
    raw_row = _make_db_row(
        donor_id=donor_id,
        donor_name="Donor",
        donor_email="donor@example.it",
        donor_country="IT",
        tax_id_type=None,
        currency="EUR",
        donation_count=None,
        total_amount_cents=None,
    )
    mock_result = MagicMock()
    mock_result.all.return_value = [raw_row]
    db.execute.return_value = mock_result

    result = await get_eu_tax_export(db, year=2025)

    assert result.rows[0].donation_count == 0
    assert result.rows[0].total_amount_cents == 0


@pytest.mark.asyncio
async def test_get_eu_tax_export_generated_at_is_iso8601() -> None:
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = []
    db.execute.return_value = mock_result

    result = await get_eu_tax_export(db, year=2025)

    # Should not raise — valid ISO 8601
    datetime.fromisoformat(result.generated_at)


@pytest.mark.asyncio
async def test_get_eu_tax_export_null_country_renders_empty_string() -> None:
    db = AsyncMock()
    raw_row = _make_db_row(
        donor_id=uuid4(),
        donor_name="Donor",
        donor_email="donor@example.com",
        donor_country=None,
        tax_id_type=None,
        currency="EUR",
        donation_count=1,
        total_amount_cents=1000,
    )
    mock_result = MagicMock()
    mock_result.all.return_value = [raw_row]
    db.execute.return_value = mock_result

    result = await get_eu_tax_export(db, year=2025)

    assert result.rows[0].donor_country == ""
