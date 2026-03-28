"""Pydantic schemas for voucher financial reconciliation endpoints."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VoucherFinanceSummary(BaseModel):
    """Aggregate financial summary for the voucher program."""

    total_purchased: int = Field(..., description="Total vouchers purchased (all time)")
    total_redeemed: int = Field(..., description="Total vouchers redeemed")
    total_expired: int = Field(..., description="Total vouchers expired")
    total_cancelled: int = Field(..., description="Total vouchers cancelled")
    total_active: int = Field(..., description="Vouchers in purchased/assigned status")
    redemption_rate_pct: float = Field(..., description="Redeemed / (Redeemed + Expired + Active)")
    total_collected_pyg: int = Field(..., description="Sum of all voucher purchase amounts (PYG)")
    total_owed_to_clinics_pyg: int = Field(
        ..., description="Sum of redeemed voucher amounts owed to clinics (PYG)"
    )
    total_collected_eur: float = Field(
        ..., description="Sum of all voucher EUR amounts (where available)"
    )


class ClinicFinanceRow(BaseModel):
    """Per-clinic financial breakdown row."""

    clinic_id: UUID
    clinic_name: str
    active_vouchers: int = Field(
        ..., description="Vouchers in purchased/assigned status for clinic"
    )
    redeemed_vouchers: int = Field(..., description="Vouchers redeemed at this clinic")
    expired_vouchers: int = Field(
        ..., description="Vouchers expired that were restricted to clinic"
    )
    amount_redeemed_pyg: int = Field(..., description="Sum of redeemed voucher amounts (PYG)")
    amount_redeemed_eur: float = Field(..., description="Sum of redeemed voucher EUR amounts")


class ClinicFinanceListResponse(BaseModel):
    """Paginated list of clinic financial breakdowns."""

    items: list[ClinicFinanceRow]
    total: int
    page: int
    page_size: int


class VoucherDetailRow(BaseModel):
    """Single voucher detail for clinic detail view."""

    voucher_id: UUID
    code: str
    status: str
    amount_pyg: int
    amount_eur: float | None
    donor_id: UUID | None
    purchased_at: datetime
    redeemed_at: datetime | None
    expires_at: datetime


class ClinicDetailResponse(BaseModel):
    """Detailed financial view for a single clinic."""

    clinic_id: UUID
    clinic_name: str
    total_redeemed_pyg: int
    total_redeemed_eur: float
    redeemed_count: int
    active_count: int
    expired_count: int
    vouchers: list[VoucherDetailRow]


class MonthlySettlementRow(BaseModel):
    """One month of settlement data."""

    month: str = Field(..., description="YYYY-MM format")
    total_redeemed_count: int
    total_redeemed_pyg: int
    total_redeemed_eur: float


class SettlementReportResponse(BaseModel):
    """Monthly settlement report."""

    start_date: date
    end_date: date
    rows: list[MonthlySettlementRow]
    total_redeemed_pyg: int
    total_redeemed_eur: float
