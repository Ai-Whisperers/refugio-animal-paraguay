"""Unit tests for RAP-611: Expense approval workflow.

Tests cover:
- Threshold-based approval determination
- Approve/reject service functions
- Escalation logic
- Notification content
- API endpoints
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.services.expense_approval import (
    DEFAULT_APPROVAL_THRESHOLD_EUR,
    DEFAULT_APPROVAL_THRESHOLD_PYG,
    ESCALATION_DAYS,
    ApprovalThresholdConfig,
    ExpenseApprovalStatus,
    approve_expense,
    build_approval_notification_body,
    build_approval_notification_subject,
    calculate_days_pending,
    determine_approval_status,
    needs_escalation,
    reject_expense,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Threshold determination tests
# ---------------------------------------------------------------------------


class TestDetermineApprovalStatus:
    """Tests for determine_approval_status()."""

    def test_below_pyg_threshold_auto_approved(self) -> None:
        result = determine_approval_status(400_000, "PYG")
        assert result == ExpenseApprovalStatus.AUTO_APPROVED

    def test_at_pyg_threshold_auto_approved(self) -> None:
        result = determine_approval_status(DEFAULT_APPROVAL_THRESHOLD_PYG, "PYG")
        assert result == ExpenseApprovalStatus.AUTO_APPROVED

    def test_above_pyg_threshold_pending(self) -> None:
        result = determine_approval_status(DEFAULT_APPROVAL_THRESHOLD_PYG + 1, "PYG")
        assert result == ExpenseApprovalStatus.PENDING

    def test_below_eur_threshold_auto_approved(self) -> None:
        result = determine_approval_status(50_00, "EUR")
        assert result == ExpenseApprovalStatus.AUTO_APPROVED

    def test_at_eur_threshold_auto_approved(self) -> None:
        result = determine_approval_status(DEFAULT_APPROVAL_THRESHOLD_EUR, "EUR")
        assert result == ExpenseApprovalStatus.AUTO_APPROVED

    def test_above_eur_threshold_pending(self) -> None:
        result = determine_approval_status(DEFAULT_APPROVAL_THRESHOLD_EUR + 1, "EUR")
        assert result == ExpenseApprovalStatus.PENDING

    def test_custom_config(self) -> None:
        config = ApprovalThresholdConfig(threshold_pyg=100_000, threshold_eur_cents=50_00)
        assert determine_approval_status(150_000, "PYG", config) == ExpenseApprovalStatus.PENDING
        assert (
            determine_approval_status(50_00, "EUR", config) == ExpenseApprovalStatus.AUTO_APPROVED
        )

    def test_usd_uses_pyg_threshold(self) -> None:
        result = determine_approval_status(DEFAULT_APPROVAL_THRESHOLD_PYG + 1, "USD")
        assert result == ExpenseApprovalStatus.PENDING


# ---------------------------------------------------------------------------
# Approve / Reject service tests
# ---------------------------------------------------------------------------


class TestApproveExpense:
    """Tests for approve_expense()."""

    def test_approve_pending(self) -> None:
        result = approve_expense(uuid4(), uuid4(), ExpenseApprovalStatus.PENDING)
        assert result.new_status == ExpenseApprovalStatus.APPROVED
        assert result.previous_status == ExpenseApprovalStatus.PENDING

    def test_approve_rejected_allowed(self) -> None:
        result = approve_expense(uuid4(), uuid4(), ExpenseApprovalStatus.REJECTED)
        assert result.new_status == ExpenseApprovalStatus.APPROVED

    def test_approve_auto_approved_fails(self) -> None:
        with pytest.raises(ValueError, match="Cannot approve"):
            approve_expense(uuid4(), uuid4(), ExpenseApprovalStatus.AUTO_APPROVED)

    def test_approve_already_approved_fails(self) -> None:
        with pytest.raises(ValueError, match="Cannot approve"):
            approve_expense(uuid4(), uuid4(), ExpenseApprovalStatus.APPROVED)

    def test_result_contains_admin_id(self) -> None:
        admin_id = uuid4()
        result = approve_expense(uuid4(), admin_id, ExpenseApprovalStatus.PENDING)
        assert result.actioned_by == admin_id

    def test_result_contains_timestamp(self) -> None:
        result = approve_expense(uuid4(), uuid4(), ExpenseApprovalStatus.PENDING)
        assert result.actioned_at is not None


class TestRejectExpense:
    """Tests for reject_expense()."""

    def test_reject_pending(self) -> None:
        result = reject_expense(uuid4(), uuid4(), ExpenseApprovalStatus.PENDING, "Too expensive")
        assert result.new_status == ExpenseApprovalStatus.REJECTED
        assert result.rejection_reason == "Too expensive"

    def test_reject_non_pending_fails(self) -> None:
        with pytest.raises(ValueError, match="Cannot reject"):
            reject_expense(uuid4(), uuid4(), ExpenseApprovalStatus.APPROVED, "Reason")

    def test_reject_empty_reason_fails(self) -> None:
        with pytest.raises(ValueError, match="Rejection reason"):
            reject_expense(uuid4(), uuid4(), ExpenseApprovalStatus.PENDING, "")

    def test_reject_whitespace_reason_fails(self) -> None:
        with pytest.raises(ValueError, match="Rejection reason"):
            reject_expense(uuid4(), uuid4(), ExpenseApprovalStatus.PENDING, "   ")

    def test_reject_strips_reason(self) -> None:
        result = reject_expense(uuid4(), uuid4(), ExpenseApprovalStatus.PENDING, "  reason  ")
        assert result.rejection_reason == "reason"


# ---------------------------------------------------------------------------
# Escalation tests
# ---------------------------------------------------------------------------


class TestEscalation:
    """Tests for escalation logic."""

    def test_days_pending_zero_for_new(self) -> None:
        now = datetime.now(UTC)
        assert calculate_days_pending(now) == 0

    def test_days_pending_correct(self) -> None:
        three_days_ago = datetime.now(UTC) - timedelta(days=3)
        assert calculate_days_pending(three_days_ago) == 3

    def test_needs_escalation_false_below_threshold(self) -> None:
        recent = datetime.now(UTC) - timedelta(days=ESCALATION_DAYS - 1)
        assert needs_escalation(recent) is False

    def test_needs_escalation_true_at_threshold(self) -> None:
        old = datetime.now(UTC) - timedelta(days=ESCALATION_DAYS)
        assert needs_escalation(old) is True

    def test_needs_escalation_true_above_threshold(self) -> None:
        old = datetime.now(UTC) - timedelta(days=ESCALATION_DAYS + 5)
        assert needs_escalation(old) is True


# ---------------------------------------------------------------------------
# Notification tests
# ---------------------------------------------------------------------------


class TestNotificationContent:
    """Tests for notification email content."""

    def test_subject_in_spanish(self) -> None:
        subject = build_approval_notification_subject()
        assert "solicitud de aprobacion" in subject

    def test_body_contains_description(self) -> None:
        body = build_approval_notification_body(
            description="Vet supplies",
            amount_cents=600_000,
            currency="PYG",
            category="medical",
            requester_name="Maria",
            expense_id=uuid4(),
        )
        assert "Vet supplies" in body

    def test_body_contains_amount(self) -> None:
        body = build_approval_notification_body(
            description="Test",
            amount_cents=600_000,
            currency="PYG",
            category="medical",
            requester_name="Maria",
            expense_id=uuid4(),
        )
        assert "600,000" in body
        assert "PYG" in body

    def test_body_contains_approve_link(self) -> None:
        eid = uuid4()
        body = build_approval_notification_body(
            description="Test",
            amount_cents=1,
            currency="PYG",
            category="other",
            requester_name="Test",
            expense_id=eid,
        )
        assert f"/admin/expenses/{eid}/approve" in body

    def test_body_contains_reject_link(self) -> None:
        eid = uuid4()
        body = build_approval_notification_body(
            description="Test",
            amount_cents=1,
            currency="PYG",
            category="other",
            requester_name="Test",
            expense_id=eid,
        )
        assert f"/admin/expenses/{eid}/reject" in body

    def test_body_contains_requester_name(self) -> None:
        body = build_approval_notification_body(
            description="Test",
            amount_cents=1,
            currency="PYG",
            category="other",
            requester_name="Carlos Fernandez",
            expense_id=uuid4(),
        )
        assert "Carlos Fernandez" in body

    def test_body_contains_category(self) -> None:
        body = build_approval_notification_body(
            description="Test",
            amount_cents=1,
            currency="PYG",
            category="transport",
            requester_name="Test",
            expense_id=uuid4(),
        )
        assert "transport" in body


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestExpenseApprovalAPI:
    """Tests for expense approval API endpoints."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import create_app

        app = create_app()
        return TestClient(app)

    def test_get_threshold(self, client: TestClient) -> None:
        response = client.get("/api/admin/expense-approvals/threshold")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "threshold_pyg" in data
        assert "threshold_eur_cents" in data

    def test_update_threshold(self, client: TestClient) -> None:
        response = client.put(
            "/api/admin/expense-approvals/threshold",
            json={"threshold_pyg": 1_000_000, "threshold_eur_cents": 200_00},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["threshold_pyg"] == 1_000_000

    def test_check_approval_required(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/expense-approvals/check",
            params={"amount_cents": 1_000_000, "currency": "PYG"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_approve_expense(self, client: TestClient) -> None:
        eid = uuid4()
        response = client.post(
            f"/api/admin/expense-approvals/{eid}/approve",
            json={"admin_id": str(uuid4())},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["new_status"] == "approved"

    def test_reject_expense(self, client: TestClient) -> None:
        eid = uuid4()
        response = client.post(
            f"/api/admin/expense-approvals/{eid}/reject",
            json={"admin_id": str(uuid4()), "reason": "Budget exceeded"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["new_status"] == "rejected"

    def test_reject_without_reason_fails(self, client: TestClient) -> None:
        eid = uuid4()
        response = client.post(
            f"/api/admin/expense-approvals/{eid}/reject",
            json={"admin_id": str(uuid4()), "reason": ""},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_bulk_approve(self, client: TestClient) -> None:
        eids = [str(uuid4()) for _ in range(3)]
        response = client.post(
            "/api/admin/expense-approvals/bulk-approve",
            json={"expense_ids": eids, "admin_id": str(uuid4())},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["approved"] == 3

    def test_notification_preview(self, client: TestClient) -> None:
        response = client.get("/api/admin/expense-approvals/notification-preview")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "subject" in data
        assert "body" in data
        assert "aprobacion" in data["subject"]


# ---------------------------------------------------------------------------
# Module structure tests
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Tests for file existence and registration."""

    def test_service_exists(self) -> None:
        assert (PROJECT_ROOT / "src" / "services" / "expense_approval.py").exists()

    def test_api_exists(self) -> None:
        assert (PROJECT_ROOT / "src" / "api" / "expense_approval.py").exists()

    def test_registered_in_app(self) -> None:
        app_source = (PROJECT_ROOT / "src" / "app.py").read_text()
        assert "expense_approval_router" in app_source

    def test_default_threshold_pyg(self) -> None:
        assert DEFAULT_APPROVAL_THRESHOLD_PYG == 500_000

    def test_default_threshold_eur(self) -> None:
        assert DEFAULT_APPROVAL_THRESHOLD_EUR == 100_00

    def test_escalation_days(self) -> None:
        assert ESCALATION_DAYS == 5
