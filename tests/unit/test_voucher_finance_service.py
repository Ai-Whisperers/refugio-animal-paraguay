"""Unit tests for voucher financial reconciliation service."""

from datetime import UTC, date

from src.schemas.voucher_finance import (
    MonthlySettlementRow,
    SettlementReportResponse,
)
from src.services.voucher_finance_service import format_settlement_csv


class TestFormatSettlementCsv:
    """Tests for CSV export formatting."""

    def test_empty_report(self) -> None:
        """Empty report should have header + total row only."""
        report = SettlementReportResponse(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            rows=[],
            total_redeemed_pyg=0,
            total_redeemed_eur=0.0,
        )
        csv_output = format_settlement_csv(report)
        lines = csv_output.strip().split("\n")
        assert len(lines) == 2  # header + total
        assert "Month" in lines[0]
        assert "TOTAL" in lines[1]
        assert ",0," in lines[1]

    def test_single_month(self) -> None:
        """Single month row should appear between header and total."""
        report = SettlementReportResponse(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            rows=[
                MonthlySettlementRow(
                    month="2026-01",
                    total_redeemed_count=5,
                    total_redeemed_pyg=500000,
                    total_redeemed_eur=75.50,
                ),
            ],
            total_redeemed_pyg=500000,
            total_redeemed_eur=75.50,
        )
        csv_output = format_settlement_csv(report)
        lines = csv_output.strip().split("\n")
        assert len(lines) == 3  # header + 1 row + total
        assert "2026-01" in lines[1]
        assert "500000" in lines[1]
        assert "75.5" in lines[1]
        assert "TOTAL" in lines[2]

    def test_multiple_months(self) -> None:
        """Multiple months should produce one row per month plus total."""
        rows = [
            MonthlySettlementRow(
                month="2026-01",
                total_redeemed_count=3,
                total_redeemed_pyg=300000,
                total_redeemed_eur=45.00,
            ),
            MonthlySettlementRow(
                month="2026-02",
                total_redeemed_count=7,
                total_redeemed_pyg=700000,
                total_redeemed_eur=105.00,
            ),
            MonthlySettlementRow(
                month="2026-03",
                total_redeemed_count=2,
                total_redeemed_pyg=200000,
                total_redeemed_eur=30.00,
            ),
        ]
        report = SettlementReportResponse(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            rows=rows,
            total_redeemed_pyg=1200000,
            total_redeemed_eur=180.00,
        )
        csv_output = format_settlement_csv(report)
        lines = csv_output.strip().split("\n")
        assert len(lines) == 5  # header + 3 months + total
        # Verify total row
        total_line = lines[-1]
        assert "TOTAL" in total_line
        assert "12" in total_line  # sum of counts
        assert "1200000" in total_line

    def test_csv_header_columns(self) -> None:
        """CSV header should have the expected columns."""
        report = SettlementReportResponse(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            rows=[],
            total_redeemed_pyg=0,
            total_redeemed_eur=0.0,
        )
        csv_output = format_settlement_csv(report)
        header = csv_output.strip().split("\n")[0]
        assert "Month" in header
        assert "Total Redeemed" in header
        assert "Amount (PYG)" in header
        assert "Amount (EUR)" in header

    def test_csv_is_valid_format(self) -> None:
        """CSV output should be parseable."""
        import csv
        import io

        report = SettlementReportResponse(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 28),
            rows=[
                MonthlySettlementRow(
                    month="2026-01",
                    total_redeemed_count=10,
                    total_redeemed_pyg=1000000,
                    total_redeemed_eur=150.00,
                ),
            ],
            total_redeemed_pyg=1000000,
            total_redeemed_eur=150.00,
        )
        csv_output = format_settlement_csv(report)
        reader = csv.reader(io.StringIO(csv_output))
        parsed_rows = list(reader)
        assert len(parsed_rows) == 3
        assert parsed_rows[0] == ["Month", "Total Redeemed", "Amount (PYG)", "Amount (EUR)"]
        assert parsed_rows[1][0] == "2026-01"
        assert parsed_rows[1][1] == "10"


class TestVoucherFinanceSummarySchema:
    """Tests for VoucherFinanceSummary schema validation."""

    def test_valid_summary(self) -> None:
        """Valid summary data should create schema instance."""
        from src.schemas.voucher_finance import VoucherFinanceSummary

        summary = VoucherFinanceSummary(
            total_purchased=100,
            total_redeemed=60,
            total_expired=10,
            total_cancelled=5,
            total_active=25,
            redemption_rate_pct=63.16,
            total_collected_pyg=10000000,
            total_owed_to_clinics_pyg=6000000,
            total_collected_eur=1500.00,
        )
        assert summary.total_purchased == 100
        assert summary.redemption_rate_pct == 63.16


class TestClinicFinanceSchemas:
    """Tests for clinic finance schema validation."""

    def test_clinic_finance_row(self) -> None:
        """ClinicFinanceRow should accept valid data."""
        from uuid import uuid4

        from src.schemas.voucher_finance import ClinicFinanceRow

        row = ClinicFinanceRow(
            clinic_id=uuid4(),
            clinic_name="Veterinaria Central",
            active_vouchers=5,
            redeemed_vouchers=15,
            expired_vouchers=2,
            amount_redeemed_pyg=1500000,
            amount_redeemed_eur=225.50,
        )
        assert row.clinic_name == "Veterinaria Central"
        assert row.redeemed_vouchers == 15

    def test_clinic_detail_response(self) -> None:
        """ClinicDetailResponse should accept valid data with voucher list."""
        from datetime import datetime
        from uuid import uuid4

        from src.schemas.voucher_finance import ClinicDetailResponse, VoucherDetailRow

        voucher = VoucherDetailRow(
            voucher_id=uuid4(),
            code="VV-TEST1234",
            status="redeemed",
            amount_pyg=100000,
            amount_eur=15.00,
            donor_id=uuid4(),
            purchased_at=datetime(2026, 1, 15, tzinfo=UTC),
            redeemed_at=datetime(2026, 2, 1, tzinfo=UTC),
            expires_at=datetime(2026, 7, 15, tzinfo=UTC),
        )
        detail = ClinicDetailResponse(
            clinic_id=uuid4(),
            clinic_name="Vet Asuncion",
            total_redeemed_pyg=100000,
            total_redeemed_eur=15.00,
            redeemed_count=1,
            active_count=3,
            expired_count=0,
            vouchers=[voucher],
        )
        assert detail.clinic_name == "Vet Asuncion"
        assert len(detail.vouchers) == 1
        assert detail.vouchers[0].code == "VV-TEST1234"


class TestSettlementReportSchema:
    """Tests for SettlementReportResponse schema."""

    def test_report_date_range(self) -> None:
        """Report should store date range correctly."""
        from src.schemas.voucher_finance import SettlementReportResponse

        report = SettlementReportResponse(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            rows=[],
            total_redeemed_pyg=0,
            total_redeemed_eur=0.0,
        )
        assert report.start_date == date(2026, 1, 1)
        assert report.end_date == date(2026, 6, 30)
        assert len(report.rows) == 0
