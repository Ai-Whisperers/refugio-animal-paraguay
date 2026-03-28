"""Tests for survey results analytics dashboard (RAP-615)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Module structure tests
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify survey_analytics module exists and is properly configured."""

    def test_module_file_exists(self) -> None:
        path = Path("src/api/survey_analytics.py")
        assert path.exists(), f"Module file missing: {path}"

    def test_module_imports(self) -> None:
        from src.api.survey_analytics import router

        assert router is not None

    def test_router_prefix(self) -> None:
        from src.api.survey_analytics import router

        assert router.prefix == "/api/admin/surveys"

    def test_router_tags(self) -> None:
        from src.api.survey_analytics import router

        assert "survey-analytics" in router.tags

    def test_registered_in_app(self) -> None:
        content = Path("src/app.py").read_text()
        assert "survey_analytics_router" in content


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify module constants."""

    def test_completion_rate_precision(self) -> None:
        from src.api.survey_analytics import COMPLETION_RATE_PRECISION

        assert COMPLETION_RATE_PRECISION == 1

    def test_percentage_precision(self) -> None:
        from src.api.survey_analytics import PERCENTAGE_PRECISION

        assert PERCENTAGE_PRECISION == 1

    def test_max_export_rows(self) -> None:
        from src.api.survey_analytics import MAX_EXPORT_ROWS

        assert MAX_EXPORT_ROWS == 10_000

    def test_min_responses_for_trend(self) -> None:
        from src.api.survey_analytics import MIN_RESPONSES_FOR_TREND

        assert MIN_RESPONSES_FOR_TREND == 2

    def test_trend_period_days(self) -> None:
        from src.api.survey_analytics import TREND_PERIOD_DAYS

        assert TREND_PERIOD_DAYS == 7

    def test_export_format_enum(self) -> None:
        from src.api.survey_analytics import ExportFormat

        assert ExportFormat.CSV == "csv"
        assert ExportFormat.JSON == "json"

    def test_trend_direction_enum(self) -> None:
        from src.api.survey_analytics import TrendDirection

        assert TrendDirection.UP == "up"
        assert TrendDirection.DOWN == "down"
        assert TrendDirection.STABLE == "stable"


# ---------------------------------------------------------------------------
# Question analytics computation tests
# ---------------------------------------------------------------------------


class TestComputeQuestionAnalytics:
    """Test compute_question_analytics function."""

    def test_no_responses(self) -> None:
        from src.api.survey_analytics import compute_question_analytics

        question = {"id": "q1", "text": "Rate us", "type": "rating", "options": []}
        result = compute_question_analytics(question, [], "survey-1")
        assert result.total_answers == 0
        assert result.average_rating is None

    def test_single_choice_breakdown(self) -> None:
        from src.api.survey_analytics import compute_question_analytics

        question = {
            "id": "q1",
            "text": "Favorite?",
            "type": "single_choice",
            "options": [{"label": "A"}, {"label": "B"}],
        }
        responses = [
            {"survey_id": "s1", "answers": {"q1": "A"}},
            {"survey_id": "s1", "answers": {"q1": "A"}},
            {"survey_id": "s1", "answers": {"q1": "B"}},
        ]
        result = compute_question_analytics(question, responses, "s1")
        assert result.total_answers == 3
        assert len(result.choice_breakdown) == 2
        a_choice = next(cb for cb in result.choice_breakdown if cb.option == "A")
        assert a_choice.count == 2
        assert a_choice.percentage == pytest.approx(66.7, abs=0.1)

    def test_multiple_choice_breakdown(self) -> None:
        from src.api.survey_analytics import compute_question_analytics

        question = {
            "id": "q1",
            "text": "Select all",
            "type": "multiple_choice",
            "options": [{"label": "X"}, {"label": "Y"}, {"label": "Z"}],
        }
        responses = [
            {"survey_id": "s1", "answers": {"q1": ["X", "Y"]}},
            {"survey_id": "s1", "answers": {"q1": ["Y", "Z"]}},
        ]
        result = compute_question_analytics(question, responses, "s1")
        assert result.total_answers == 2
        y_choice = next(cb for cb in result.choice_breakdown if cb.option == "Y")
        assert y_choice.count == 2

    def test_rating_average(self) -> None:
        from src.api.survey_analytics import compute_question_analytics

        question = {"id": "q1", "text": "Rate", "type": "rating", "options": []}
        responses = [
            {"survey_id": "s1", "answers": {"q1": 4}},
            {"survey_id": "s1", "answers": {"q1": 5}},
            {"survey_id": "s1", "answers": {"q1": 3}},
        ]
        result = compute_question_analytics(question, responses, "s1")
        assert result.average_rating == 4.0
        assert len(result.choice_breakdown) == 5  # ratings 1-5

    def test_text_responses_collected(self) -> None:
        from src.api.survey_analytics import compute_question_analytics

        question = {"id": "q1", "text": "Comments?", "type": "text", "options": []}
        responses = [
            {"survey_id": "s1", "answers": {"q1": "Great service"}},
            {"survey_id": "s1", "answers": {"q1": "Needs improvement"}},
        ]
        result = compute_question_analytics(question, responses, "s1")
        assert result.total_answers == 2
        assert "Great service" in result.text_responses
        assert "Needs improvement" in result.text_responses

    def test_yes_no_breakdown(self) -> None:
        from src.api.survey_analytics import compute_question_analytics

        question = {
            "id": "q1",
            "text": "Recommend?",
            "type": "yes_no",
            "options": [{"label": "Si"}, {"label": "No"}],
        }
        responses = [
            {"survey_id": "s1", "answers": {"q1": "Si"}},
            {"survey_id": "s1", "answers": {"q1": "Si"}},
            {"survey_id": "s1", "answers": {"q1": "No"}},
        ]
        result = compute_question_analytics(question, responses, "s1")
        assert result.total_answers == 3
        si_choice = next(cb for cb in result.choice_breakdown if cb.option == "Si")
        assert si_choice.count == 2

    def test_filters_by_survey_id(self) -> None:
        from src.api.survey_analytics import compute_question_analytics

        question = {"id": "q1", "text": "Rate", "type": "rating", "options": []}
        responses = [
            {"survey_id": "s1", "answers": {"q1": 5}},
            {"survey_id": "s2", "answers": {"q1": 1}},  # Different survey
        ]
        result = compute_question_analytics(question, responses, "s1")
        assert result.total_answers == 1


# ---------------------------------------------------------------------------
# Response trends tests
# ---------------------------------------------------------------------------


class TestComputeResponseTrends:
    """Test response trend computation."""

    def test_empty_responses(self) -> None:
        from src.api.survey_analytics import compute_response_trends

        trends, direction = compute_response_trends([], "s1")
        assert trends == []
        assert direction == "stable"

    def test_single_week(self) -> None:
        from src.api.survey_analytics import compute_response_trends

        responses = [
            {"survey_id": "s1", "submitted_at": "2026-03-15T10:00:00"},
            {"survey_id": "s1", "submitted_at": "2026-03-15T11:00:00"},
        ]
        trends, direction = compute_response_trends(responses, "s1")
        assert len(trends) >= 1
        assert trends[0].count == 2
        assert direction == "stable"  # only 1 period, not enough for trend

    def test_multiple_weeks_up_trend(self) -> None:
        from src.api.survey_analytics import compute_response_trends

        responses = [
            {"survey_id": "s1", "submitted_at": "2026-03-02T10:00:00"},
            {"survey_id": "s1", "submitted_at": "2026-03-09T10:00:00"},
            {"survey_id": "s1", "submitted_at": "2026-03-10T10:00:00"},
            {"survey_id": "s1", "submitted_at": "2026-03-11T10:00:00"},
        ]
        trends, direction = compute_response_trends(responses, "s1")
        assert len(trends) >= 2
        assert direction == "up"

    def test_down_trend(self) -> None:
        from src.api.survey_analytics import compute_response_trends

        responses = [
            {"survey_id": "s1", "submitted_at": "2026-03-02T10:00:00"},
            {"survey_id": "s1", "submitted_at": "2026-03-03T10:00:00"},
            {"survey_id": "s1", "submitted_at": "2026-03-04T10:00:00"},
            {"survey_id": "s1", "submitted_at": "2026-03-15T11:00:00"},
        ]
        trends, direction = compute_response_trends(responses, "s1")
        assert len(trends) >= 2
        assert direction == "down"


# ---------------------------------------------------------------------------
# Generate survey analytics tests
# ---------------------------------------------------------------------------


class TestGenerateSurveyAnalytics:
    """Test the full analytics generation."""

    def _mock_stores(self):
        """Return sample survey store and responses."""
        surveys = {
            "s1": {
                "id": "s1",
                "title": "Encuesta de satisfaccion",
                "status": "active",
                "questions": [
                    {
                        "id": "q1",
                        "text": "Rate our service",
                        "type": "rating",
                        "required": True,
                        "options": [],
                    },
                    {
                        "id": "q2",
                        "text": "Comments",
                        "type": "text",
                        "required": False,
                        "options": [],
                    },
                ],
                "response_count": 2,
            }
        }
        responses = [
            {
                "survey_id": "s1",
                "answers": {"q1": 5, "q2": "Excellent"},
                "submitted_at": "2026-03-15T10:00:00",
            },
            {"survey_id": "s1", "answers": {"q1": 4}, "submitted_at": "2026-03-16T10:00:00"},
        ]
        return surveys, responses

    def test_returns_summary(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        surveys, responses = self._mock_stores()
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, responses)):
            result = generate_survey_analytics("s1")
        assert result.survey_id == "s1"
        assert result.total_responses == 2

    def test_completion_rate(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        surveys, responses = self._mock_stores()
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, responses)):
            result = generate_survey_analytics("s1")
        # Both responses have q1 (required), so 100% completion
        assert result.completion_rate == 100.0

    def test_partial_completion(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        surveys = {
            "s1": {
                "id": "s1",
                "title": "Test",
                "questions": [
                    {"id": "q1", "text": "Q1", "type": "text", "required": True, "options": []},
                    {"id": "q2", "text": "Q2", "type": "text", "required": True, "options": []},
                ],
            }
        }
        responses = [
            {
                "survey_id": "s1",
                "answers": {"q1": "a", "q2": "b"},
                "submitted_at": "2026-03-15T10:00:00",
            },
            {"survey_id": "s1", "answers": {"q1": "a"}, "submitted_at": "2026-03-16T10:00:00"},
        ]
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, responses)):
            result = generate_survey_analytics("s1")
        assert result.completion_rate == 50.0

    def test_question_analytics_populated(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        surveys, responses = self._mock_stores()
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, responses)):
            result = generate_survey_analytics("s1")
        assert len(result.questions) == 2
        assert result.questions[0].question_id == "q1"

    def test_survey_not_found_raises(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        with (
            patch("src.api.survey_analytics._get_survey_store", return_value=({}, [])),
            pytest.raises(ValueError, match="not found"),
        ):
            generate_survey_analytics("nonexistent")

    def test_last_response_at(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        surveys, responses = self._mock_stores()
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, responses)):
            result = generate_survey_analytics("s1")
        assert result.last_response_at == "2026-03-16T10:00:00"

    def test_generated_at_populated(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        surveys, responses = self._mock_stores()
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, responses)):
            result = generate_survey_analytics("s1")
        assert result.generated_at != ""

    def test_zero_responses(self) -> None:
        from src.api.survey_analytics import generate_survey_analytics

        surveys = {"s1": {"id": "s1", "title": "Empty", "questions": []}}
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, [])):
            result = generate_survey_analytics("s1")
        assert result.total_responses == 0
        assert result.completion_rate == 0.0
        assert result.last_response_at is None


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------


class TestExportSurveyResponses:
    """Test export functionality."""

    def test_export_json(self) -> None:
        from src.api.survey_analytics import ExportFormat, export_survey_responses

        surveys = {
            "s1": {
                "id": "s1",
                "title": "Test",
                "questions": [{"id": "q1", "text": "Q1", "type": "text", "options": []}],
            }
        }
        responses = [
            {
                "survey_id": "s1",
                "id": "r1",
                "answers": {"q1": "hello"},
                "submitted_at": "2026-03-15",
            },
        ]
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, responses)):
            result = export_survey_responses("s1", ExportFormat.JSON)
        assert result.format == "json"
        assert result.row_count == 1
        assert result.data[0]["Q1"] == "hello"

    def test_export_not_found(self) -> None:
        from src.api.survey_analytics import export_survey_responses

        with (
            patch("src.api.survey_analytics._get_survey_store", return_value=({}, [])),
            pytest.raises(ValueError, match="not found"),
        ):
            export_survey_responses("bad")

    def test_export_empty(self) -> None:
        from src.api.survey_analytics import export_survey_responses

        surveys = {"s1": {"id": "s1", "title": "Test", "questions": []}}
        with patch("src.api.survey_analytics._get_survey_store", return_value=(surveys, [])):
            result = export_survey_responses("s1")
        assert result.row_count == 0
        assert result.data == []


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


class TestSurveyAnalyticsAPI:
    """Test API endpoints via TestClient."""

    @pytest.fixture()
    def client(self) -> TestClient:
        from src.app import create_app

        app = create_app()
        return TestClient(app)

    def test_analytics_endpoint_with_sample(self, client: TestClient) -> None:
        resp = client.get("/api/admin/surveys/survey-satisfaccion/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["survey_id"] == "survey-satisfaccion"
        assert "total_responses" in data
        assert "questions" in data

    def test_analytics_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/admin/surveys/nonexistent/analytics")
        assert resp.status_code == 404

    def test_export_endpoint(self, client: TestClient) -> None:
        resp = client.get("/api/admin/surveys/survey-satisfaccion/export?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "json"
        assert "row_count" in data

    def test_export_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/admin/surveys/nonexistent/export")
        assert resp.status_code == 404

    def test_summary_endpoint(self, client: TestClient) -> None:
        resp = client.get("/api/admin/surveys/survey-satisfaccion/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_responses" in data
        assert "completion_rate" in data
        assert "trend_direction" in data

    def test_summary_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/admin/surveys/nonexistent/summary")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Frontend page tests
# ---------------------------------------------------------------------------


class TestSurveyResultsPage:
    """Test frontend survey results page."""

    @pytest.fixture()
    def page_content(self) -> str:
        return Path("frontend/src/app/admin/encuestas/resultados/page.tsx").read_text()

    def test_file_exists(self) -> None:
        assert Path("frontend/src/app/admin/encuestas/resultados/page.tsx").exists()

    def test_is_client_component(self, page_content: str) -> None:
        assert '"use client"' in page_content

    def test_has_page_title(self, page_content: str) -> None:
        assert "Resultados de Encuesta" in page_content

    def test_has_metric_card_component(self, page_content: str) -> None:
        assert "MetricCard" in page_content

    def test_has_horizontal_bar_chart(self, page_content: str) -> None:
        assert "HorizontalBarChart" in page_content

    def test_has_rating_display(self, page_content: str) -> None:
        assert "RatingDisplay" in page_content

    def test_has_text_response_list(self, page_content: str) -> None:
        assert "TextResponseList" in page_content

    def test_has_trend_chart(self, page_content: str) -> None:
        assert "TrendChart" in page_content

    def test_has_question_card(self, page_content: str) -> None:
        assert "QuestionCard" in page_content

    def test_has_loading_skeleton(self, page_content: str) -> None:
        assert "LoadingSkeleton" in page_content

    def test_has_error_state(self, page_content: str) -> None:
        assert "ErrorState" in page_content

    def test_has_export_buttons(self, page_content: str) -> None:
        assert "Exportar JSON" in page_content
        assert "Exportar CSV" in page_content

    def test_has_refresh_button(self, page_content: str) -> None:
        assert "Actualizar" in page_content

    def test_fetches_analytics_api(self, page_content: str) -> None:
        assert "/api/admin/surveys/" in page_content
        assert "/analytics" in page_content

    def test_has_spanish_labels(self, page_content: str) -> None:
        assert "Total respuestas" in page_content
        assert "Tasa de completado" in page_content
        assert "Resultados por pregunta" in page_content

    def test_has_rating_labels(self, page_content: str) -> None:
        assert "Muy malo" in page_content
        assert "Excelente" in page_content

    def test_has_trend_direction_labels(self, page_content: str) -> None:
        assert "En aumento" in page_content
        assert "Disminuyendo" in page_content
        assert "Estable" in page_content

    def test_has_chart_colors(self, page_content: str) -> None:
        assert "CHART_COLORS" in page_content

    def test_has_question_type_labels(self, page_content: str) -> None:
        assert "Opcion unica" in page_content
        assert "Opcion multiple" in page_content
        assert "Puntuacion" in page_content
        assert "Texto libre" in page_content


# ---------------------------------------------------------------------------
# Accessibility tests
# ---------------------------------------------------------------------------


class TestSurveyResultsAccessibility:
    """Test accessibility features of the results page."""

    @pytest.fixture()
    def page_content(self) -> str:
        return Path("frontend/src/app/admin/encuestas/resultados/page.tsx").read_text()

    def test_aria_labels_present(self, page_content: str) -> None:
        assert "aria-label" in page_content

    def test_bar_chart_has_role_img(self, page_content: str) -> None:
        assert 'role="img"' in page_content

    def test_error_state_has_role_alert(self, page_content: str) -> None:
        assert 'role="alert"' in page_content

    def test_text_responses_has_role_list(self, page_content: str) -> None:
        assert 'role="list"' in page_content
        assert 'role="listitem"' in page_content

    def test_loading_has_aria_busy(self, page_content: str) -> None:
        assert "aria-busy" in page_content

    def test_touch_targets(self, page_content: str) -> None:
        assert "min-h-[44px]" in page_content
        assert "min-w-[44px]" in page_content

    def test_show_more_has_aria_expanded(self, page_content: str) -> None:
        assert "aria-expanded" in page_content
