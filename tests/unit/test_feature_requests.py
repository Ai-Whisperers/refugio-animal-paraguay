"""Tests for RAP-616: Community feature request board.

Covers API endpoints and frontend page structure.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_FILE = PROJECT_ROOT / "src" / "api" / "feature_requests.py"
FRONTEND_FILE = PROJECT_ROOT / "frontend" / "src" / "app" / "comunidad" / "solicitudes" / "page.tsx"
APP_FILE = PROJECT_ROOT / "src" / "app.py"


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify module files and registration."""

    def test_api_file_exists(self) -> None:
        assert API_FILE.exists()

    def test_frontend_file_exists(self) -> None:
        assert FRONTEND_FILE.exists()

    def test_registered_in_app(self) -> None:
        content = APP_FILE.read_text()
        assert "feature_requests_router" in content

    def test_router_prefix(self) -> None:
        from src.api.feature_requests import router

        assert router.prefix == "/api/feature-requests"

    def test_router_tags(self) -> None:
        from src.api.feature_requests import router

        assert "feature-requests" in router.tags


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify API constants."""

    def test_max_title_length(self) -> None:
        from src.api.feature_requests import MAX_TITLE_LENGTH

        assert MAX_TITLE_LENGTH == 120

    def test_max_description_length(self) -> None:
        from src.api.feature_requests import MAX_DESCRIPTION_LENGTH

        assert MAX_DESCRIPTION_LENGTH == 1000

    def test_request_status_values(self) -> None:
        from src.api.feature_requests import RequestStatus

        assert RequestStatus.OPEN == "open"
        assert RequestStatus.COMPLETED == "completed"
        assert RequestStatus.DECLINED == "declined"

    def test_request_categories(self) -> None:
        from src.api.feature_requests import RequestCategory

        assert RequestCategory.ADOPTION == "adopcion"
        assert RequestCategory.DONATIONS == "donaciones"
        assert RequestCategory.OTHER == "otro"

    def test_category_labels_spanish(self) -> None:
        from src.api.feature_requests import CATEGORY_LABELS_ES

        assert CATEGORY_LABELS_ES["adopcion"] == "Adopcion"
        assert CATEGORY_LABELS_ES["donaciones"] == "Donaciones"

    def test_status_labels_spanish(self) -> None:
        from src.api.feature_requests import STATUS_LABELS_ES

        assert STATUS_LABELS_ES["open"] == "Abierto"
        assert STATUS_LABELS_ES["completed"] == "Completado"


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestFeatureRequestsAPI:
    """Test API endpoints."""

    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from src.api.feature_requests import _reset_store

        _reset_store()

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import app

        return TestClient(app)

    def _create_request(self, client: TestClient, **overrides: str) -> dict:
        payload = {
            "title": "Agregar fotos de animales en adopcion",
            "description": "Me gustaria ver mas fotos de los animales disponibles para adopcion",
            "category": "animales",
            "submitted_by_name": "Maria",
            "submitted_by_email": "maria@example.com",
            **overrides,
        }
        response = client.post("/api/feature-requests", json=payload)
        return response.json()

    def test_create_request(self, client: TestClient) -> None:
        response = client.post(
            "/api/feature-requests",
            json={
                "title": "Agregar fotos de animales",
                "description": "Me gustaria ver mas fotos de los animales disponibles",
                "category": "animales",
                "submitted_by_name": "Maria",
                "submitted_by_email": "maria@example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["status"] == "open"
        assert data["votes"] == 0

    def test_create_request_validation(self, client: TestClient) -> None:
        response = client.post(
            "/api/feature-requests",
            json={
                "title": "Hi",
                "description": "Short",
                "category": "animales",
                "submitted_by_name": "X",
                "submitted_by_email": "x@x.com",
            },
        )
        assert response.status_code == 422

    def test_list_empty(self, client: TestClient) -> None:
        response = client.get("/api/feature-requests")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_requests(self, client: TestClient) -> None:
        self._create_request(client)
        self._create_request(client, title="Otra solicitud interesante")
        response = client.get("/api/feature-requests")
        data = response.json()
        assert data["total"] == 2

    def test_list_filter_by_category(self, client: TestClient) -> None:
        self._create_request(client, category="animales")
        self._create_request(client, category="donaciones", title="Mejorar flujo de donaciones")
        response = client.get("/api/feature-requests?category=animales")
        data = response.json()
        assert data["total"] == 1

    def test_get_single_request(self, client: TestClient) -> None:
        self._create_request(client)
        response = client.get("/api/feature-requests/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1

    def test_get_nonexistent_404(self, client: TestClient) -> None:
        response = client.get("/api/feature-requests/999")
        assert response.status_code == 404

    def test_vote_for_request(self, client: TestClient) -> None:
        self._create_request(client)
        response = client.post("/api/feature-requests/1/vote?voter_key=user1")
        assert response.status_code == 200
        data = response.json()
        assert data["votes"] == 1
        assert "Voto" in data["message"]

    def test_duplicate_vote_rejected(self, client: TestClient) -> None:
        self._create_request(client)
        client.post("/api/feature-requests/1/vote?voter_key=user1")
        response = client.post("/api/feature-requests/1/vote?voter_key=user1")
        assert response.status_code == 409

    def test_vote_nonexistent_404(self, client: TestClient) -> None:
        response = client.post("/api/feature-requests/999/vote")
        assert response.status_code == 404

    def test_list_categories(self, client: TestClient) -> None:
        response = client.get("/api/feature-requests/categories/list")
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) == 7
        assert any(c["value"] == "adopcion" for c in categories)

    def test_sort_by_votes(self, client: TestClient) -> None:
        self._create_request(client, title="Solicitud con pocos votos")
        self._create_request(client, title="Solicitud popular entre usuarios")
        client.post("/api/feature-requests/2/vote?voter_key=u1")
        client.post("/api/feature-requests/2/vote?voter_key=u2")
        response = client.get("/api/feature-requests?sort_by=votes")
        items = response.json()["items"]
        assert items[0]["id"] == 2

    def test_pagination(self, client: TestClient) -> None:
        for i in range(5):
            self._create_request(client, title=f"Solicitud numero {i + 1} para prueba")
        response = client.get("/api/feature-requests?page_size=2&page=1")
        data = response.json()
        assert len(data["items"]) == 2
        assert data["has_more"] is True


# ---------------------------------------------------------------------------
# Frontend page
# ---------------------------------------------------------------------------


class TestFeatureRequestBoardPage:
    """Verify frontend page structure."""

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.content = FRONTEND_FILE.read_text()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.content

    def test_page_title(self) -> None:
        assert "Tablero de Solicitudes" in self.content

    def test_submit_form(self) -> None:
        assert "SubmitForm" in self.content

    def test_request_card(self) -> None:
        assert "RequestCard" in self.content

    def test_vote_button(self) -> None:
        assert "VoteButton" in self.content

    def test_status_badge(self) -> None:
        assert "StatusBadge" in self.content

    def test_categories_defined(self) -> None:
        assert "CATEGORIES" in self.content

    def test_form_fields(self) -> None:
        assert "Titulo" in self.content
        assert "Descripcion" in self.content
        assert "Categoria" in self.content

    def test_submit_button_spanish(self) -> None:
        assert "Enviar solicitud" in self.content

    def test_cancel_button(self) -> None:
        assert "Cancelar" in self.content

    def test_empty_state(self) -> None:
        assert "No hay solicitudes" in self.content

    def test_filter_controls(self) -> None:
        assert "Todas las categorias" in self.content
        assert "Mas votados" in self.content
        assert "Mas recientes" in self.content

    def test_success_feedback(self) -> None:
        assert "Solicitud enviada exitosamente" in self.content

    def test_error_feedback(self) -> None:
        assert "Error al enviar" in self.content


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------


class TestFeatureRequestAccessibility:
    """Verify WCAG compliance."""

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.content = FRONTEND_FILE.read_text()

    def test_aria_labels(self) -> None:
        assert "aria-label" in self.content

    def test_role_alert(self) -> None:
        assert 'role="alert"' in self.content

    def test_role_list(self) -> None:
        assert 'role="list"' in self.content

    def test_role_listitem(self) -> None:
        assert 'role="listitem"' in self.content

    def test_min_touch_targets(self) -> None:
        assert "min-h-[44px]" in self.content

    def test_form_labels(self) -> None:
        assert "htmlFor" in self.content

    def test_section_landmarks(self) -> None:
        assert "<section" in self.content
