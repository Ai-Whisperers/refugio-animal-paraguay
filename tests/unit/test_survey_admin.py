"""Tests for admin survey creation form (RAP-613)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Module structure tests
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify survey_admin module exists and is properly configured."""

    def test_module_file_exists(self) -> None:
        path = Path("src/api/survey_admin.py")
        assert path.exists(), f"Module file missing: {path}"

    def test_module_imports(self) -> None:
        from src.api.survey_admin import router

        assert router is not None

    def test_router_prefix(self) -> None:
        from src.api.survey_admin import router

        assert router.prefix == "/api/admin/survey-management"

    def test_router_tags(self) -> None:
        from src.api.survey_admin import router

        assert "survey-admin" in router.tags

    def test_registered_in_app(self) -> None:
        content = Path("src/app.py").read_text()
        assert "survey_admin_router" in content


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify module constants."""

    def test_max_title_length(self) -> None:
        from src.api.survey_admin import MAX_TITLE_LENGTH

        assert MAX_TITLE_LENGTH == 200

    def test_max_description_length(self) -> None:
        from src.api.survey_admin import MAX_DESCRIPTION_LENGTH

        assert MAX_DESCRIPTION_LENGTH == 2000

    def test_max_questions(self) -> None:
        from src.api.survey_admin import MAX_QUESTIONS_PER_SURVEY

        assert MAX_QUESTIONS_PER_SURVEY == 50

    def test_max_options(self) -> None:
        from src.api.survey_admin import MAX_OPTIONS_PER_QUESTION

        assert MAX_OPTIONS_PER_QUESTION == 20

    def test_min_title_length(self) -> None:
        from src.api.survey_admin import MIN_TITLE_LENGTH

        assert MIN_TITLE_LENGTH == 3

    def test_survey_status_enum(self) -> None:
        from src.api.survey_admin import SurveyAdminStatus

        assert SurveyAdminStatus.DRAFT == "draft"
        assert SurveyAdminStatus.ACTIVE == "active"
        assert SurveyAdminStatus.CLOSED == "closed"
        assert SurveyAdminStatus.ARCHIVED == "archived"

    def test_question_type_enum(self) -> None:
        from src.api.survey_admin import QuestionType

        assert QuestionType.TEXT == "text"
        assert QuestionType.SINGLE_CHOICE == "single_choice"
        assert QuestionType.RATING == "rating"
        assert QuestionType.YES_NO == "yes_no"

    def test_question_type_labels_spanish(self) -> None:
        from src.api.survey_admin import QUESTION_TYPE_LABELS_ES

        assert "text" in QUESTION_TYPE_LABELS_ES
        assert len(QUESTION_TYPE_LABELS_ES) == 5


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    """Test survey validation logic."""

    def test_valid_survey(self) -> None:
        from src.api.survey_admin import SurveyCreateRequest, _validate_survey

        req = SurveyCreateRequest(title="Test survey", questions=[])
        errors = _validate_survey(req)
        assert errors == []

    def test_choice_question_needs_options(self) -> None:
        from src.api.survey_admin import (
            QuestionInput,
            SurveyCreateRequest,
            _validate_survey,
        )

        req = SurveyCreateRequest(
            title="Test",
            questions=[
                QuestionInput(text="Pick one", question_type="single_choice", options=[]),
            ],
        )
        errors = _validate_survey(req)
        assert any("opciones" in e for e in errors)

    def test_date_validation(self) -> None:
        from src.api.survey_admin import SurveyCreateRequest, _validate_survey

        req = SurveyCreateRequest(
            title="Test",
            start_date="2026-12-31",
            end_date="2026-01-01",
        )
        errors = _validate_survey(req)
        assert any("fecha" in e.lower() for e in errors)

    def test_too_many_questions(self) -> None:
        from src.api.survey_admin import (
            QuestionInput,
            SurveyCreateRequest,
            _validate_survey,
        )

        questions = [QuestionInput(text=f"Q{i}") for i in range(51)]
        req = SurveyCreateRequest(title="Test", questions=questions)
        errors = _validate_survey(req)
        assert any("50" in e for e in errors)


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestSurveyAdminAPI:
    """Test API endpoints via TestClient."""

    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        from src.api.survey_admin import _reset_store

        _reset_store()

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import create_app

        app = create_app()
        return TestClient(app)

    def test_create_draft_survey(self, client: TestClient) -> None:
        resp = client.post(
            "/api/admin/survey-management",
            json={
                "title": "Encuesta de prueba",
                "description": "Descripcion",
                "questions": [
                    {"text": "Como nos encontraste?", "question_type": "text"},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["title"] == "Encuesta de prueba"
        assert len(data["questions"]) == 1

    def test_create_with_choice_questions(self, client: TestClient) -> None:
        resp = client.post(
            "/api/admin/survey-management",
            json={
                "title": "Test choices",
                "questions": [
                    {
                        "text": "Favorite animal?",
                        "question_type": "single_choice",
                        "options": [
                            {"label": "Perro"},
                            {"label": "Gato"},
                            {"label": "Otro"},
                        ],
                    },
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["questions"][0]["options"]) == 3

    def test_create_invalid_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/api/admin/survey-management",
            json={
                "title": "Test",
                "questions": [
                    {"text": "Pick", "question_type": "single_choice", "options": []},
                ],
            },
        )
        assert resp.status_code == 422

    def test_list_surveys_empty(self, client: TestClient) -> None:
        resp = client.get("/api/admin/survey-management")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["surveys"] == []

    def test_list_surveys_after_create(self, client: TestClient) -> None:
        client.post(
            "/api/admin/survey-management",
            json={"title": "Survey 1", "questions": [{"text": "Q1"}]},
        )
        client.post(
            "/api/admin/survey-management",
            json={"title": "Survey 2", "questions": [{"text": "Q2"}]},
        )
        resp = client.get("/api/admin/survey-management")
        assert resp.json()["total"] == 2

    def test_get_survey(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={"title": "My Survey", "questions": [{"text": "Q1"}]},
        )
        survey_id = create_resp.json()["id"]
        resp = client.get(f"/api/admin/survey-management/{survey_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "My Survey"

    def test_get_nonexistent(self, client: TestClient) -> None:
        resp = client.get("/api/admin/survey-management/bad-id")
        assert resp.status_code == 404

    def test_update_survey(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={"title": "Original", "questions": [{"text": "Q1"}]},
        )
        survey_id = create_resp.json()["id"]
        resp = client.put(
            f"/api/admin/survey-management/{survey_id}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_publish_survey(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={"title": "Draft Survey", "questions": [{"text": "Q1"}]},
        )
        survey_id = create_resp.json()["id"]
        resp = client.post(f"/api/admin/survey-management/{survey_id}/publish")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_publish_without_questions_fails(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={"title": "Empty Survey"},
        )
        survey_id = create_resp.json()["id"]
        resp = client.post(f"/api/admin/survey-management/{survey_id}/publish")
        assert resp.status_code == 400

    def test_publish_non_draft_fails(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={"title": "Test", "questions": [{"text": "Q1"}]},
        )
        survey_id = create_resp.json()["id"]
        # Publish once
        client.post(f"/api/admin/survey-management/{survey_id}/publish")
        # Try again
        resp = client.post(f"/api/admin/survey-management/{survey_id}/publish")
        assert resp.status_code == 400

    def test_clone_survey(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={
                "title": "Original Survey",
                "questions": [{"text": "Q1"}, {"text": "Q2"}],
            },
        )
        original_id = create_resp.json()["id"]
        resp = client.post(f"/api/admin/survey-management/{original_id}/clone")
        assert resp.status_code == 201
        data = resp.json()
        assert "(Copia)" in data["title"]
        assert data["status"] == "draft"
        assert data["id"] != original_id
        assert len(data["questions"]) == 2

    def test_clone_nonexistent(self, client: TestClient) -> None:
        resp = client.post("/api/admin/survey-management/bad-id/clone")
        assert resp.status_code == 404

    def test_close_survey(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={"title": "Test", "questions": [{"text": "Q1"}]},
        )
        survey_id = create_resp.json()["id"]
        client.post(f"/api/admin/survey-management/{survey_id}/publish")
        resp = client.post(f"/api/admin/survey-management/{survey_id}/close")
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    def test_close_non_active_fails(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/admin/survey-management",
            json={"title": "Draft", "questions": [{"text": "Q1"}]},
        )
        survey_id = create_resp.json()["id"]
        resp = client.post(f"/api/admin/survey-management/{survey_id}/close")
        assert resp.status_code == 400

    def test_filter_by_status(self, client: TestClient) -> None:
        client.post(
            "/api/admin/survey-management",
            json={"title": "Draft 1", "questions": [{"text": "Q1"}]},
        )
        create2 = client.post(
            "/api/admin/survey-management",
            json={"title": "To Publish", "questions": [{"text": "Q1"}]},
        )
        client.post(f"/api/admin/survey-management/{create2.json()['id']}/publish")
        resp = client.get("/api/admin/survey-management?status=active")
        assert resp.json()["total"] == 1
        assert resp.json()["surveys"][0]["status"] == "active"


# ---------------------------------------------------------------------------
# Frontend page tests
# ---------------------------------------------------------------------------


class TestAdminSurveyCreationPage:
    """Test frontend admin survey creation page."""

    @pytest.fixture()
    def page_content(self) -> str:
        return Path("frontend/src/app/admin/encuestas/nueva/page.tsx").read_text()

    def test_file_exists(self) -> None:
        assert Path("frontend/src/app/admin/encuestas/nueva/page.tsx").exists()

    def test_is_client_component(self, page_content: str) -> None:
        assert '"use client"' in page_content

    def test_has_page_title(self, page_content: str) -> None:
        assert "Crear nueva encuesta" in page_content

    def test_has_question_builder(self, page_content: str) -> None:
        assert "QuestionBuilder" in page_content

    def test_has_survey_preview(self, page_content: str) -> None:
        assert "SurveyPreview" in page_content

    def test_has_question_types(self, page_content: str) -> None:
        assert "Texto libre" in page_content
        assert "Opcion unica" in page_content
        assert "Opcion multiple" in page_content
        assert "Puntuacion" in page_content

    def test_has_form_fields(self, page_content: str) -> None:
        assert "survey-title" in page_content
        assert "survey-desc" in page_content
        assert "start-date" in page_content
        assert "end-date" in page_content

    def test_has_add_question_button(self, page_content: str) -> None:
        assert "Agregar pregunta" in page_content

    def test_has_save_buttons(self, page_content: str) -> None:
        assert "Guardar borrador" in page_content
        assert "Publicar encuesta" in page_content

    def test_has_preview_button(self, page_content: str) -> None:
        assert "Vista previa" in page_content

    def test_has_reorder_controls(self, page_content: str) -> None:
        assert "onMoveUp" in page_content
        assert "onMoveDown" in page_content

    def test_has_required_toggle(self, page_content: str) -> None:
        assert "Obligatoria" in page_content

    def test_has_character_counters(self, page_content: str) -> None:
        assert "MAX_TITLE_LENGTH" in page_content
        assert "MAX_DESCRIPTION_LENGTH" in page_content

    def test_has_option_management(self, page_content: str) -> None:
        assert "Agregar opcion" in page_content
        assert "removeOption" in page_content

    def test_has_success_feedback(self, page_content: str) -> None:
        assert "guardada como borrador" in page_content
        assert "publicada exitosamente" in page_content

    def test_has_empty_state(self, page_content: str) -> None:
        assert "No hay preguntas" in page_content

    def test_has_api_integration(self, page_content: str) -> None:
        assert "/api/admin/survey-management" in page_content


# ---------------------------------------------------------------------------
# Accessibility tests
# ---------------------------------------------------------------------------


class TestSurveyCreationAccessibility:
    """Test accessibility features."""

    @pytest.fixture()
    def page_content(self) -> str:
        return Path("frontend/src/app/admin/encuestas/nueva/page.tsx").read_text()

    def test_aria_labels_present(self, page_content: str) -> None:
        assert "aria-label" in page_content

    def test_form_labels_with_htmlfor(self, page_content: str) -> None:
        assert "htmlFor" in page_content

    def test_preview_dialog_role(self, page_content: str) -> None:
        assert 'role="dialog"' in page_content

    def test_alert_role_for_feedback(self, page_content: str) -> None:
        assert 'role="alert"' in page_content

    def test_question_group_role(self, page_content: str) -> None:
        assert 'role="group"' in page_content

    def test_touch_targets(self, page_content: str) -> None:
        assert "min-h-[44px]" in page_content
        assert "min-w-[44px]" in page_content

    def test_disabled_states(self, page_content: str) -> None:
        assert "disabled:opacity" in page_content
