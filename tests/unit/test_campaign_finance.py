"""Tests for RAP-607: Campaign-specific financial reports.

Covers allocation validation, service logic, and API endpoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SERVICE_FILE = PROJECT_ROOT / "src" / "services" / "campaign_finance.py"
API_FILE = PROJECT_ROOT / "src" / "api" / "campaign_finance.py"
APP_FILE = PROJECT_ROOT / "src" / "app.py"


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify module files and registration."""

    def test_service_file_exists(self) -> None:
        assert SERVICE_FILE.exists()

    def test_api_file_exists(self) -> None:
        assert API_FILE.exists()

    def test_registered_in_app(self) -> None:
        content = APP_FILE.read_text()
        assert "campaign_finance_router" in content
        assert "from src.api.campaign_finance import" in content

    def test_router_prefix(self) -> None:
        from src.api.campaign_finance import router

        assert router.prefix == "/api/admin/campaigns"

    def test_router_tags(self) -> None:
        from src.api.campaign_finance import router

        assert "campaign-finance" in router.tags


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_max_allocations(self) -> None:
        from src.services.campaign_finance import MAX_ALLOCATIONS_PER_EXPENSE

        assert MAX_ALLOCATIONS_PER_EXPENSE == 10

    def test_min_percentage(self) -> None:
        from src.services.campaign_finance import MIN_ALLOCATION_PERCENTAGE

        assert MIN_ALLOCATION_PERCENTAGE == 1.0

    def test_max_percentage(self) -> None:
        from src.services.campaign_finance import MAX_ALLOCATION_PERCENTAGE

        assert MAX_ALLOCATION_PERCENTAGE == 100.0

    def test_allocation_status_values(self) -> None:
        from src.services.campaign_finance import AllocationStatus

        assert AllocationStatus.ACTIVE == "active"
        assert AllocationStatus.REVOKED == "revoked"

    def test_expense_categories(self) -> None:
        from src.services.campaign_finance import EXPENSE_CATEGORIES

        assert len(EXPENSE_CATEGORIES) == 7
        assert "medical" in EXPENSE_CATEGORIES
        assert "food" in EXPENSE_CATEGORIES

    def test_category_labels_spanish(self) -> None:
        from src.services.campaign_finance import CATEGORY_LABELS_ES

        assert CATEGORY_LABELS_ES["medical"] == "Medico"
        assert CATEGORY_LABELS_ES["food"] == "Comida"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestAllocationValidation:
    """Test allocation percentage validation."""

    def test_valid_single_allocation(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages([{"campaign_id": "c1", "percentage": 100.0}])
        assert valid
        assert _msg == ""

    def test_valid_split_allocation(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages(
            [
                {"campaign_id": "c1", "percentage": 60.0},
                {"campaign_id": "c2", "percentage": 40.0},
            ]
        )
        assert valid

    def test_empty_allocations_rejected(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages([])
        assert not valid
        assert "al menos una" in _msg

    def test_exceeds_100_percent(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages(
            [
                {"campaign_id": "c1", "percentage": 60.0},
                {"campaign_id": "c2", "percentage": 50.0},
            ]
        )
        assert not valid
        assert "100%" in _msg

    def test_duplicate_campaign_rejected(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages(
            [
                {"campaign_id": "c1", "percentage": 50.0},
                {"campaign_id": "c1", "percentage": 50.0},
            ]
        )
        assert not valid
        assert "duplicada" in _msg.lower()

    def test_below_minimum_percentage(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages([{"campaign_id": "c1", "percentage": 0.5}])
        assert not valid

    def test_above_maximum_percentage(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages([{"campaign_id": "c1", "percentage": 101.0}])
        assert not valid

    def test_missing_campaign_id(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        valid, _msg = validate_allocation_percentages([{"campaign_id": "", "percentage": 50.0}])
        assert not valid

    def test_too_many_allocations(self) -> None:
        from src.services.campaign_finance import validate_allocation_percentages

        allocs = [{"campaign_id": f"c{i}", "percentage": 5.0} for i in range(11)]
        valid, _msg = validate_allocation_percentages(allocs)
        assert not valid
        assert "10" in _msg


# ---------------------------------------------------------------------------
# Allocation service
# ---------------------------------------------------------------------------


class TestAllocateExpense:
    """Test expense allocation logic."""

    def test_successful_allocation(self) -> None:
        from src.services.campaign_finance import (
            AllocationRequest,
            allocate_expense_to_campaigns,
        )

        request = AllocationRequest(
            expense_id="exp-1",
            expense_amount_pyg=1_000_000,
            allocations=[{"campaign_id": "c1", "percentage": 100.0}],
        )
        result = allocate_expense_to_campaigns(request)
        assert result.success
        assert len(result.allocations) == 1
        assert result.allocations[0].amount_pyg == 1_000_000

    def test_split_allocation_amounts(self) -> None:
        from src.services.campaign_finance import (
            AllocationRequest,
            allocate_expense_to_campaigns,
        )

        request = AllocationRequest(
            expense_id="exp-2",
            expense_amount_pyg=1_000_000,
            allocations=[
                {"campaign_id": "c1", "percentage": 60.0},
                {"campaign_id": "c2", "percentage": 40.0},
            ],
        )
        result = allocate_expense_to_campaigns(request)
        assert result.success
        assert result.allocations[0].amount_pyg == 600_000
        assert result.allocations[1].amount_pyg == 400_000
        assert result.total_allocated_percentage == 100.0

    def test_invalid_allocation_fails(self) -> None:
        from src.services.campaign_finance import (
            AllocationRequest,
            allocate_expense_to_campaigns,
        )

        request = AllocationRequest(
            expense_id="exp-3",
            expense_amount_pyg=1_000_000,
            allocations=[],
        )
        result = allocate_expense_to_campaigns(request)
        assert not result.success

    def test_custom_allocated_by(self) -> None:
        from src.services.campaign_finance import (
            AllocationRequest,
            allocate_expense_to_campaigns,
        )

        request = AllocationRequest(
            expense_id="exp-4",
            expense_amount_pyg=500_000,
            allocations=[{"campaign_id": "c1", "percentage": 100.0}],
        )
        result = allocate_expense_to_campaigns(request, allocated_by="ivan")
        assert result.allocations[0].allocated_by == "ivan"

    def test_message_spanish(self) -> None:
        from src.services.campaign_finance import (
            AllocationRequest,
            allocate_expense_to_campaigns,
        )

        request = AllocationRequest(
            expense_id="exp-5",
            expense_amount_pyg=500_000,
            allocations=[{"campaign_id": "c1", "percentage": 100.0}],
        )
        result = allocate_expense_to_campaigns(request)
        assert "campanas" in result.message.lower()


# ---------------------------------------------------------------------------
# Campaign financial summary
# ---------------------------------------------------------------------------


class TestCampaignFinancialSummary:
    """Test campaign report generation."""

    def test_empty_campaign_report(self) -> None:
        from src.services.campaign_finance import generate_campaign_financial_summary

        summary = generate_campaign_financial_summary(
            campaign_id="c1",
            campaign_name="Test Campaign",
            total_raised_pyg=5_000_000,
        )
        assert summary.campaign_id == "c1"
        assert summary.total_raised_pyg == 5_000_000
        assert summary.total_spent_pyg == 0
        assert summary.remaining_balance_pyg == 5_000_000

    def test_with_allocations(self) -> None:
        from src.services.campaign_finance import (
            AllocationStatus,
            ExpenseAllocation,
            generate_campaign_financial_summary,
        )

        allocs = [
            ExpenseAllocation(
                expense_id="e1",
                campaign_id="c1",
                percentage=100.0,
                amount_pyg=1_000_000,
                status=AllocationStatus.ACTIVE,
            ),
            ExpenseAllocation(
                expense_id="e2",
                campaign_id="c1",
                percentage=50.0,
                amount_pyg=500_000,
                status=AllocationStatus.ACTIVE,
            ),
        ]
        summary = generate_campaign_financial_summary(
            campaign_id="c1",
            total_raised_pyg=3_000_000,
            allocations=allocs,
        )
        assert summary.total_spent_pyg == 1_500_000
        assert summary.remaining_balance_pyg == 1_500_000
        assert summary.expense_count == 2

    def test_revoked_allocations_excluded(self) -> None:
        from src.services.campaign_finance import (
            AllocationStatus,
            ExpenseAllocation,
            generate_campaign_financial_summary,
        )

        allocs = [
            ExpenseAllocation(
                expense_id="e1",
                campaign_id="c1",
                percentage=100.0,
                amount_pyg=1_000_000,
                status=AllocationStatus.REVOKED,
            ),
        ]
        summary = generate_campaign_financial_summary(
            campaign_id="c1",
            total_raised_pyg=3_000_000,
            allocations=allocs,
        )
        assert summary.total_spent_pyg == 0

    def test_usd_conversion(self) -> None:
        from src.services.campaign_finance import generate_campaign_financial_summary

        summary = generate_campaign_financial_summary(
            campaign_id="c1",
            total_raised_pyg=1_000_000,
        )
        assert summary.total_raised_usd > 0

    def test_category_breakdown_with_allocations(self) -> None:
        from src.services.campaign_finance import (
            ExpenseAllocation,
            generate_campaign_financial_summary,
        )

        allocs = [
            ExpenseAllocation(
                expense_id=f"e{i}",
                campaign_id="c1",
                percentage=100.0,
                amount_pyg=100_000,
            )
            for i in range(3)
        ]
        summary = generate_campaign_financial_summary(
            campaign_id="c1",
            total_raised_pyg=1_000_000,
            allocations=allocs,
        )
        assert len(summary.category_breakdown) > 0


# ---------------------------------------------------------------------------
# Format allocation summary
# ---------------------------------------------------------------------------


class TestFormatAllocationSummary:
    """Test allocation summary formatting."""

    def test_empty_allocations(self) -> None:
        from src.services.campaign_finance import format_allocation_summary

        assert format_allocation_summary([]) == "Sin asignaciones"

    def test_single_allocation(self) -> None:
        from src.services.campaign_finance import (
            ExpenseAllocation,
            format_allocation_summary,
        )

        allocs = [
            ExpenseAllocation(campaign_id="c1", percentage=100.0),
        ]
        result = format_allocation_summary(allocs)
        assert "100%" in result
        assert "c1" in result

    def test_multiple_allocations(self) -> None:
        from src.services.campaign_finance import (
            ExpenseAllocation,
            format_allocation_summary,
        )

        allocs = [
            ExpenseAllocation(campaign_id="c1", percentage=60.0),
            ExpenseAllocation(campaign_id="c2", percentage=40.0),
        ]
        result = format_allocation_summary(allocs)
        assert "60%" in result
        assert "40%" in result
        assert ", " in result


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestCampaignFinanceAPI:
    """Test API endpoints."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.api.campaign_finance import _allocations
        from src.app import app

        _allocations.clear()
        return TestClient(app)

    def test_allocate_expense(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/campaigns/camp-1/expenses/allocate",
            json={
                "expense_id": "exp-1",
                "expense_amount_pyg": 1_000_000,
                "allocations": [{"campaign_id": "camp-1", "percentage": 100.0}],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["allocation_count"] == 1

    def test_allocate_invalid_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/campaigns/camp-1/expenses/allocate",
            json={
                "expense_id": "exp-1",
                "expense_amount_pyg": 1_000_000,
                "allocations": [
                    {"campaign_id": "c1", "percentage": 80.0},
                    {"campaign_id": "c2", "percentage": 80.0},
                ],
            },
        )
        assert response.status_code == 422

    def test_get_financial_report(self, client: TestClient) -> None:
        response = client.get(
            "/api/admin/campaigns/camp-1/financial-report?campaign_name=Test&total_raised_pyg=5000000"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["campaign_id"] == "camp-1"
        assert data["total_raised_pyg"] == 5_000_000

    def test_get_allocations_empty(self, client: TestClient) -> None:
        response = client.get("/api/admin/campaigns/camp-1/allocations")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_allocations_after_create(self, client: TestClient) -> None:
        client.post(
            "/api/admin/campaigns/camp-1/expenses/allocate",
            json={
                "expense_id": "exp-1",
                "expense_amount_pyg": 1_000_000,
                "allocations": [{"campaign_id": "camp-1", "percentage": 100.0}],
            },
        )
        response = client.get("/api/admin/campaigns/camp-1/allocations")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_revoke_allocation(self, client: TestClient) -> None:
        # Create allocation first
        client.post(
            "/api/admin/campaigns/camp-1/expenses/allocate",
            json={
                "expense_id": "exp-1",
                "expense_amount_pyg": 1_000_000,
                "allocations": [{"campaign_id": "camp-1", "percentage": 100.0}],
            },
        )
        allocs = client.get("/api/admin/campaigns/camp-1/allocations").json()
        alloc_id = allocs[0]["id"]

        response = client.delete(f"/api/admin/campaigns/camp-1/allocations/{alloc_id}")
        assert response.status_code == 200
        assert "revocada" in response.json()["message"].lower()

    def test_revoke_nonexistent_404(self, client: TestClient) -> None:
        response = client.delete("/api/admin/campaigns/camp-1/allocations/nonexistent")
        assert response.status_code == 404
