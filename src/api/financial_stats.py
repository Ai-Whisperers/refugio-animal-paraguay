"""Public financial transparency statistics API.

Provides aggregated financial data for the public transparency dashboard.
No authentication required — all data is pre-approved and safe to display.
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/stats", tags=["financial-stats"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_TTL_SECONDS: int = 3600  # 1 hour
PYG_TO_USD_RATE: float = 0.000137  # approximate, updated periodically
MONTHS_HISTORY: int = 12

MONTH_NAMES_ES: list[str] = [
    "",
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]


class ExpenseCategoryLabel(enum.StrEnum):
    """Expense categories with Spanish display names."""

    MEDICAL = "Medico"
    FOOD = "Comida"
    SHELTER = "Refugio"
    RESCUE = "Rescate"
    OPERATIONS = "Operaciones"
    TRANSPORT = "Transporte"
    ADMINISTRATION = "Administracion"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CurrencyAmount(BaseModel):
    """Amount in PYG with USD equivalent."""

    pyg: int = Field(description="Amount in Paraguayan Guarani")
    usd: float = Field(description="Approximate USD equivalent")


class MetricCard(BaseModel):
    """Single metric for the dashboard header."""

    label_es: str
    label_en: str
    amount: CurrencyAmount


class CategoryBreakdown(BaseModel):
    """Expense breakdown for a single category."""

    category: str
    label_es: str
    amount_pyg: int
    percentage: float = Field(ge=0, le=100)


class MonthlyComparison(BaseModel):
    """Income vs expenses for a single month."""

    month: int = Field(ge=1, le=12)
    month_label: str
    income_pyg: int
    expenses_pyg: int
    net_pyg: int


class FinancialStatsResponse(BaseModel):
    """Complete financial transparency data."""

    generated_at: str
    cache_ttl_seconds: int = CACHE_TTL_SECONDS
    year: int
    disclaimer_es: str = "Todos los gastos mostrados son aprobados por la junta directiva"
    metrics: list[MetricCard]
    expense_categories: list[CategoryBreakdown]
    monthly_comparison: list[MonthlyComparison]
    last_updated: str


# ---------------------------------------------------------------------------
# Data generation (MVP — returns representative structure)
# ---------------------------------------------------------------------------

_SAMPLE_MONTHLY_INCOME: list[int] = [
    4_200_000,
    3_800_000,
    5_100_000,
    4_500_000,
    3_900_000,
    4_800_000,
    5_500_000,
    4_100_000,
    4_700_000,
    5_200_000,
    4_600_000,
    6_000_000,
]

_SAMPLE_MONTHLY_EXPENSES: list[int] = [
    3_500_000,
    3_200_000,
    4_200_000,
    3_800_000,
    3_400_000,
    4_000_000,
    4_500_000,
    3_600_000,
    3_900_000,
    4_300_000,
    3_800_000,
    5_000_000,
]

_CATEGORY_PERCENTAGES: dict[str, float] = {
    "MEDICAL": 30.0,
    "FOOD": 25.0,
    "SHELTER": 15.0,
    "RESCUE": 10.0,
    "OPERATIONS": 8.0,
    "TRANSPORT": 7.0,
    "ADMINISTRATION": 5.0,
}


def _pyg_to_usd(pyg: int) -> float:
    """Convert PYG to approximate USD."""
    return round(pyg * PYG_TO_USD_RATE, 2)


def _build_metrics(
    month_income: int,
    month_expenses: int,
    year_income: int,
    year_expenses: int,
) -> list[MetricCard]:
    """Build the 4 key metric cards."""
    return [
        MetricCard(
            label_es="Recibido este mes",
            label_en="Received this month",
            amount=CurrencyAmount(pyg=month_income, usd=_pyg_to_usd(month_income)),
        ),
        MetricCard(
            label_es="Gastado este mes",
            label_en="Spent this month",
            amount=CurrencyAmount(pyg=month_expenses, usd=_pyg_to_usd(month_expenses)),
        ),
        MetricCard(
            label_es="Recibido este ano",
            label_en="Received this year",
            amount=CurrencyAmount(pyg=year_income, usd=_pyg_to_usd(year_income)),
        ),
        MetricCard(
            label_es="Balance disponible",
            label_en="Available balance",
            amount=CurrencyAmount(
                pyg=year_income - year_expenses,
                usd=_pyg_to_usd(year_income - year_expenses),
            ),
        ),
    ]


def _build_category_breakdown(total_expenses: int) -> list[CategoryBreakdown]:
    """Build expense breakdown by category."""
    result: list[CategoryBreakdown] = []
    for cat_key, pct in _CATEGORY_PERCENTAGES.items():
        cat_enum = ExpenseCategoryLabel[cat_key]
        result.append(
            CategoryBreakdown(
                category=cat_key.lower(),
                label_es=cat_enum.value,
                amount_pyg=int(total_expenses * pct / 100),
                percentage=pct,
            )
        )
    return result


def _build_monthly_comparison(year: int) -> list[MonthlyComparison]:
    """Build 12-month income vs expenses comparison."""
    now = datetime.now(UTC)
    current_month = now.month if now.year == year else MONTHS_HISTORY
    result: list[MonthlyComparison] = []
    for i in range(MONTHS_HISTORY):
        month_num = i + 1
        income = _SAMPLE_MONTHLY_INCOME[i] if month_num <= current_month else 0
        expenses = _SAMPLE_MONTHLY_EXPENSES[i] if month_num <= current_month else 0
        result.append(
            MonthlyComparison(
                month=month_num,
                month_label=MONTH_NAMES_ES[month_num],
                income_pyg=income,
                expenses_pyg=expenses,
                net_pyg=income - expenses,
            )
        )
    return result


def generate_financial_stats(year: int | None = None) -> dict[str, Any]:
    """Generate complete financial stats response."""
    now = datetime.now(UTC)
    target_year = year if year is not None else now.year
    current_month_idx = (now.month - 1) if now.year == target_year else 11

    month_income = _SAMPLE_MONTHLY_INCOME[current_month_idx]
    month_expenses = _SAMPLE_MONTHLY_EXPENSES[current_month_idx]
    year_income = sum(_SAMPLE_MONTHLY_INCOME)
    year_expenses = sum(_SAMPLE_MONTHLY_EXPENSES)

    return FinancialStatsResponse(
        generated_at=now.isoformat(),
        year=target_year,
        metrics=_build_metrics(month_income, month_expenses, year_income, year_expenses),
        expense_categories=_build_category_breakdown(year_expenses),
        monthly_comparison=_build_monthly_comparison(target_year),
        last_updated=now.strftime("%Y-%m-%d %H:%M UTC"),
    ).model_dump()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/financial",
    response_model=FinancialStatsResponse,
    summary="Public financial transparency data",
    description="Returns aggregated financial data for the transparency dashboard. "
    "No authentication required. Data is cached for 1 hour.",
)
async def get_financial_stats(
    year: int | None = Query(
        None, ge=2020, le=2030, description="Year to report on (defaults to current)"
    ),
) -> dict[str, Any]:
    """Return financial transparency statistics."""
    return generate_financial_stats(year)
