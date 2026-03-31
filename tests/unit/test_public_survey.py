"""Tests for RAP-614: Public survey response collection.

Covers survey API and frontend page.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_FILE = PROJECT_ROOT / "src" / "api" / "public_survey.py"
FRONTEND_FILE = PROJECT_ROOT / "frontend" / "src" / "app" / "encuestas" / "page.tsx"
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
        assert "public_survey_router" in content

    def test_router_prefix(self) -> None:
        from src.api.public_survey import router

        assert router.prefix == "/api/surveys"

    def test_router_tags(self) -> None:
        from src.api.public_survey import router

        assert "public-surveys" in router.tags


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify API constants."""

    def test_question_types(self) -> None:
        from src.api.public_survey import QuestionType

        assert QuestionType.TEXT == "text"
        assert QuestionType.RATING == "rating"
        assert QuestionType.YES_NO == "yes_no"
        assert QuestionType.SINGLE_CHOICE == "single_choice"
        assert QuestionType.MULTIPLE_CHOICE == "multiple_choice"

    def test_survey_status(self) -> None:
        from src.api.public_survey import SurveyStatus

        assert SurveyStatus.ACTIVE == "active"
        assert SurveyStatus.CLOSED == "closed"

    def test_max_responses(self) -> None:
        from src.api.public_survey import MAX_RESPONSES_PER_SURVEY

        assert MAX_RESPONSES_PER_SURVEY == 10_000


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestPublicSurveyAPI:
    """Test survey API endpoints."""

    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from src.api.public_survey import _reset_store

        _reset_store()

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import app

        return TestClient(app)

    def test_list_active_surveys(self, client: TestClient) -> None:
        response = client.get("/api/surveys/active")
        assert response.status_code == 200
        surveys = response.json()
        assert isinstance(surveys, list)
        assert len(surveys) >= 1

    def test_survey_has_questions(self, client: TestClient) -> None:
        response = client.get("/api/surveys/active")
        surveys = response.json()
        assert len(surveys[0]["questions"]) > 0

    def test_get_survey_by_id(self, client: TestClient) -> None:
        response = client.get("/api/surveys/survey-satisfaccion")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "survey-satisfaccion"
        assert data["is_active"] is True

    def test_get_nonexistent_survey_404(self, client: TestClient) -> None:
        response = client.get("/api/surveys/nonexistent")
        assert response.status_code == 404

    def test_submit_response(self, client: TestClient) -> None:
        response = client.post(
            "/api/surveys/survey-satisfaccion/responses",
            json={
                "respondent_name": "Maria",
                "answers": [
                    {"question_id": "q1", "value": 5},
                    {"question_id": "q2", "value": "opt1"},
                    {"question_id": "q4", "value": "si"},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "exitosamente" in data["message"]

    def test_submit_missing_required_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/surveys/survey-satisfaccion/responses",
            json={
                "answers": [
                    {"question_id": "q5", "value": "Comentario"},
                ],
            },
        )
        assert response.status_code == 422

    def test_submit_to_nonexistent_survey(self, client: TestClient) -> None:
        response = client.post(
            "/api/surveys/nonexistent/responses",
            json={
                "answers": [{"question_id": "q1", "value": 5}],
            },
        )
        assert response.status_code == 404

    def test_response_count_increments(self, client: TestClient) -> None:
        client.post(
            "/api/surveys/survey-satisfaccion/responses",
            json={
                "answers": [
                    {"question_id": "q1", "value": 4},
                    {"question_id": "q2", "value": "opt2"},
                    {"question_id": "q4", "value": "no"},
                ],
            },
        )
        response = client.get("/api/surveys/survey-satisfaccion/response-count")
        assert response.status_code == 200
        assert response.json()["response_count"] == 1

    def test_get_response_count(self, client: TestClient) -> None:
        response = client.get("/api/surveys/survey-satisfaccion/response-count")
        assert response.status_code == 200
        data = response.json()
        assert "response_count" in data

    def test_response_count_nonexistent_404(self, client: TestClient) -> None:
        response = client.get("/api/surveys/nonexistent/response-count")
        assert response.status_code == 404

    def test_survey_questions_have_types(self, client: TestClient) -> None:
        response = client.get("/api/surveys/survey-satisfaccion")
        questions = response.json()["questions"]
        types = {q["question_type"] for q in questions}
        assert "rating" in types
        assert "single_choice" in types
        assert "yes_no" in types
        assert "text" in types

    def test_survey_has_thank_you_message(self, client: TestClient) -> None:
        response = client.get("/api/surveys/survey-satisfaccion")
        data = response.json()
        assert len(data["thank_you_message"]) > 0
        assert "Gracias" in data["thank_you_message"]


# ---------------------------------------------------------------------------
# Frontend page
# ---------------------------------------------------------------------------


class TestEncuestasPage:
    """Verify frontend page structure."""

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.content = FRONTEND_FILE.read_text()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.content

    def test_page_title(self) -> None:
        assert "Encuestas" in self.content

    def test_survey_form_component(self) -> None:
        assert "SurveyForm" in self.content

    def test_rating_input(self) -> None:
        assert "RatingInput" in self.content

    def test_yes_no_input(self) -> None:
        assert "YesNoInput" in self.content

    def test_question_renderer(self) -> None:
        assert "QuestionRenderer" in self.content

    def test_thank_you_message(self) -> None:
        assert "ThankYouMessage" in self.content
        assert "Respuesta enviada" in self.content

    def test_submit_button_spanish(self) -> None:
        assert "Enviar respuesta" in self.content

    def test_back_button(self) -> None:
        assert "Volver a la lista" in self.content

    def test_empty_state(self) -> None:
        assert "No hay encuestas activas" in self.content

    def test_loading_state(self) -> None:
        assert "animate-pulse" in self.content

    def test_error_handling(self) -> None:
        assert "Error al cargar" in self.content

    def test_estimated_time(self) -> None:
        assert "Tiempo estimado" in self.content

    def test_response_count_display(self) -> None:
        assert "respuestas" in self.content

    def test_required_indicator(self) -> None:
        assert "obligatorio" in self.content


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------


class TestEncuestasAccessibility:
    """Verify WCAG compliance."""

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        self.content = FRONTEND_FILE.read_text()

    def test_aria_labels(self) -> None:
        assert "aria-label" in self.content

    def test_role_alert(self) -> None:
        assert 'role="alert"' in self.content

    def test_role_radiogroup(self) -> None:
        assert 'role="radiogroup"' in self.content

    def test_role_list(self) -> None:
        assert 'role="list"' in self.content

    def test_min_touch_targets(self) -> None:
        assert "min-h-[44px]" in self.content

    def test_form_labels(self) -> None:
        assert "htmlFor" in self.content

    def test_section_landmarks(self) -> None:
        assert "<section" in self.content

    def test_sr_only_inputs(self) -> None:
        assert "sr-only" in self.content
