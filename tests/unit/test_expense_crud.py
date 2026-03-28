"""Unit tests for RAP-604: Expense recording system.

Tests cover:
- CRUD operations (create, read, update, delete)
- Validation (positive amount, no future dates, valid category/currency)
- Approve/reject workflow
- Filtering and pagination
- Error handling (404, 409, 400)
"""

from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestExpenseCRUD:
    """Tests for expense CRUD API endpoints."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import create_app

        app = create_app()
        return TestClient(app)

    @pytest.fixture()
    def sample_expense(self) -> dict:
        return {
            "amount_cents": 150000,
            "currency": "PYG",
            "category": "medical",
            "description": "Vacunas para gatos",
            "expense_date": date.today().isoformat(),
            "notes": "10 gatos vacunados",
        }

    # --- Create ---

    def test_create_expense(self, client: TestClient, sample_expense: dict) -> None:
        response = client.post("/api/admin/expenses", json=sample_expense)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount_cents"] == 150000
        assert data["category"] == "medical"
        assert data["status"] == "pending"

    def test_create_expense_eur(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/expenses",
            json={
                "amount_cents": 5000,
                "currency": "EUR",
                "category": "food",
                "description": "Alimento importado",
                "expense_date": date.today().isoformat(),
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["currency"] == "EUR"

    def test_create_expense_invalid_amount(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/expenses",
            json={
                "amount_cents": 0,
                "currency": "PYG",
                "category": "food",
                "description": "Test",
                "expense_date": date.today().isoformat(),
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_expense_negative_amount(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/expenses",
            json={
                "amount_cents": -100,
                "currency": "PYG",
                "category": "food",
                "description": "Test",
                "expense_date": date.today().isoformat(),
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_expense_future_date(self, client: TestClient) -> None:
        future = (date.today() + timedelta(days=10)).isoformat()
        response = client.post(
            "/api/admin/expenses",
            json={
                "amount_cents": 1000,
                "currency": "PYG",
                "category": "food",
                "description": "Test future",
                "expense_date": future,
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_expense_invalid_currency(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/expenses",
            json={
                "amount_cents": 1000,
                "currency": "GBP",
                "category": "food",
                "description": "Test",
                "expense_date": date.today().isoformat(),
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_expense_invalid_category(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/expenses",
            json={
                "amount_cents": 1000,
                "currency": "PYG",
                "category": "invalid_cat",
                "description": "Test",
                "expense_date": date.today().isoformat(),
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # --- Read ---

    def test_get_expense(self, client: TestClient, sample_expense: dict) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        response = client.get(f"/api/admin/expenses/{eid}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == eid

    def test_get_nonexistent_expense(self, client: TestClient) -> None:
        response = client.get("/api/admin/expenses/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_expenses(self, client: TestClient, sample_expense: dict) -> None:
        client.post("/api/admin/expenses", json=sample_expense)
        response = client.get("/api/admin/expenses")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_list_expenses_filter_category(self, client: TestClient, sample_expense: dict) -> None:
        client.post("/api/admin/expenses", json=sample_expense)
        response = client.get("/api/admin/expenses?category=medical")
        assert response.status_code == status.HTTP_200_OK

    def test_list_expenses_filter_status(self, client: TestClient, sample_expense: dict) -> None:
        client.post("/api/admin/expenses", json=sample_expense)
        response = client.get("/api/admin/expenses?status=pending")
        assert response.status_code == status.HTTP_200_OK

    # --- Update ---

    def test_update_expense(self, client: TestClient, sample_expense: dict) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        response = client.put(
            f"/api/admin/expenses/{eid}",
            json={"description": "Vacunas actualizadas"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["description"] == "Vacunas actualizadas"

    def test_update_nonexistent(self, client: TestClient) -> None:
        response = client.put(
            "/api/admin/expenses/99999",
            json={"description": "Test"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_approved_expense_blocked(
        self, client: TestClient, sample_expense: dict
    ) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        client.patch(f"/api/admin/expenses/{eid}/approve")
        response = client.put(
            f"/api/admin/expenses/{eid}",
            json={"description": "Should fail"},
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    # --- Delete ---

    def test_delete_expense(self, client: TestClient, sample_expense: dict) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        response = client.delete(f"/api/admin/expenses/{eid}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_nonexistent(self, client: TestClient) -> None:
        response = client.delete("/api/admin/expenses/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_approved_blocked(self, client: TestClient, sample_expense: dict) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        client.patch(f"/api/admin/expenses/{eid}/approve")
        response = client.delete(f"/api/admin/expenses/{eid}")
        assert response.status_code == status.HTTP_409_CONFLICT

    # --- Approve / Reject ---

    def test_approve_expense(self, client: TestClient, sample_expense: dict) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        response = client.patch(f"/api/admin/expenses/{eid}/approve")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "approved"

    def test_approve_nonexistent(self, client: TestClient) -> None:
        response = client.patch("/api/admin/expenses/99999/approve")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_reject_expense(self, client: TestClient, sample_expense: dict) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        response = client.patch(f"/api/admin/expenses/{eid}/reject?reason=Presupuesto+excedido")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "rejected"
        assert response.json()["rejection_reason"] == "Presupuesto excedido"

    def test_reject_nonexistent(self, client: TestClient) -> None:
        response = client.patch("/api/admin/expenses/99999/reject?reason=Test")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_approve_already_approved_blocked(
        self, client: TestClient, sample_expense: dict
    ) -> None:
        create = client.post("/api/admin/expenses", json=sample_expense)
        eid = create.json()["id"]
        client.patch(f"/api/admin/expenses/{eid}/approve")
        response = client.patch(f"/api/admin/expenses/{eid}/approve")
        assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# Module structure tests
# ---------------------------------------------------------------------------


class TestExpenseCRUDModuleStructure:
    """Verify file existence and registration."""

    def test_api_module_exists(self) -> None:
        assert (PROJECT_ROOT / "src" / "api" / "expense_crud.py").exists()

    def test_registered_in_app(self) -> None:
        app_source = (PROJECT_ROOT / "src" / "app.py").read_text()
        assert "expense_crud_router" in app_source

    def test_has_extended_categories(self) -> None:
        source = (PROJECT_ROOT / "src" / "api" / "expense_crud.py").read_text()
        for cat in ["medical", "food", "shelter", "rescue", "operations", "transport", "admin"]:
            assert cat.upper() in source or cat in source

    def test_has_spanish_error_messages(self) -> None:
        source = (PROJECT_ROOT / "src" / "api" / "expense_crud.py").read_text()
        assert "Gasto no encontrado" in source
        assert "no puede ser futura" in source
