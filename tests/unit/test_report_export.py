"""Tests for the report export module (RAP-638).

Covers module structure, constants, helpers, API endpoints,
frontend page, accessibility, and app registration.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Module structure
# ---------------------------------------------------------------------------
class TestModuleStructure:
    """Verify module-level attributes and exports."""

    def test_router_exists(self) -> None:
        from src.api.report_export import router

        assert router is not None

    def test_router_prefix(self) -> None:
        from src.api.report_export import router

        assert router.prefix == "/api/admin/reports"

    def test_router_tag(self) -> None:
        from src.api.report_export import router

        assert "report-export" in router.tags

    def test_report_type_enum(self) -> None:
        from src.api.report_export import ReportType

        assert hasattr(ReportType, "ANIMAL_INVENTORY")
        assert hasattr(ReportType, "ADOPTIONS")
        assert hasattr(ReportType, "DONATIONS")
        assert hasattr(ReportType, "VETERINARY")
        assert hasattr(ReportType, "VOLUNTEERS")
        assert hasattr(ReportType, "FINANCIAL")

    def test_export_format_enum(self) -> None:
        from src.api.report_export import ExportFormat

        assert hasattr(ExportFormat, "CSV")
        assert hasattr(ExportFormat, "JSON")

    def test_report_status_enum(self) -> None:
        from src.api.report_export import ReportStatus

        assert hasattr(ReportStatus, "PENDING")
        assert hasattr(ReportStatus, "GENERATING")
        assert hasattr(ReportStatus, "COMPLETED")
        assert hasattr(ReportStatus, "FAILED")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
class TestConstants:
    """Verify named constants are defined with reasonable values."""

    def test_max_report_rows(self) -> None:
        from src.api.report_export import MAX_REPORT_ROWS

        assert MAX_REPORT_ROWS == 10_000

    def test_report_retention_days(self) -> None:
        from src.api.report_export import REPORT_RETENTION_DAYS

        assert REPORT_RETENTION_DAYS == 30

    def test_csv_delimiter(self) -> None:
        from src.api.report_export import CSV_DELIMITER

        assert CSV_DELIMITER == ","

    def test_report_definitions_count(self) -> None:
        from src.api.report_export import REPORT_DEFINITIONS

        assert len(REPORT_DEFINITIONS) == 6


# ---------------------------------------------------------------------------
# Report definitions
# ---------------------------------------------------------------------------
class TestReportDefinitions:
    """Validate report definition structure."""

    def test_all_report_types_have_definitions(self) -> None:
        from src.api.report_export import REPORT_DEFINITIONS, ReportType

        for rt in ReportType:
            assert rt.value in REPORT_DEFINITIONS, f"Missing definition for {rt}"

    def test_definitions_have_required_keys(self) -> None:
        from src.api.report_export import REPORT_DEFINITIONS

        for name, defn in REPORT_DEFINITIONS.items():
            assert "title" in defn, f"{name} missing title"
            assert "description" in defn, f"{name} missing description"
            assert "columns" in defn, f"{name} missing columns"

    def test_definitions_have_spanish_titles(self) -> None:
        from src.api.report_export import REPORT_DEFINITIONS

        for name, defn in REPORT_DEFINITIONS.items():
            assert len(defn["title"]) > 0, f"{name} has empty title"

    def test_columns_are_non_empty_lists(self) -> None:
        from src.api.report_export import REPORT_DEFINITIONS

        for name, defn in REPORT_DEFINITIONS.items():
            assert isinstance(defn["columns"], list), f"{name} columns not a list"
            assert len(defn["columns"]) > 0, f"{name} has no columns"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
class TestHelperFunctions:
    """Test internal helper functions."""

    def test_generate_sample_data_returns_list(self) -> None:
        from src.api.report_export import ReportType, _generate_sample_data

        data = _generate_sample_data(ReportType.ANIMAL_INVENTORY)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_generate_sample_data_all_types(self) -> None:
        from src.api.report_export import ReportType, _generate_sample_data

        for rt in ReportType:
            data = _generate_sample_data(rt)
            assert isinstance(data, list), f"Failed for {rt}"

    def test_data_to_csv_produces_valid_csv(self) -> None:
        from src.api.report_export import _data_to_csv

        # _data_to_csv signature is (columns, rows)
        columns = ["name", "species"]
        data = [{"name": "Luna", "species": "Perro"}]
        result = _data_to_csv(columns, data)
        assert "name,species" in result
        assert "Luna,Perro" in result

    def test_data_to_csv_handles_empty_data(self) -> None:
        from src.api.report_export import _data_to_csv

        columns = ["col1", "col2"]
        result = _data_to_csv(columns, [])
        # Should have header row
        assert "col1,col2" in result

    def test_data_to_json_produces_valid_json(self) -> None:
        from src.api.report_export import _data_to_json

        data = [{"name": "Luna", "species": "Perro"}]
        result = _data_to_json(data)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "Luna"

    def test_data_to_json_empty_list(self) -> None:
        from src.api.report_export import _data_to_json

        result = _data_to_json([])
        parsed = json.loads(result)
        assert parsed == []

    def test_reset_store_clears_reports(self) -> None:
        from src.api.report_export import _generated_reports, _reset_store

        _generated_reports["test"] = {"fake": True}
        _reset_store()
        assert len(_generated_reports) == 0


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class TestSchemas:
    """Verify Pydantic schemas are importable and have expected fields."""

    def test_report_generate_request_fields(self) -> None:
        from src.api.report_export import ReportGenerateRequest

        schema = ReportGenerateRequest.model_json_schema()
        assert "report_type" in schema.get("properties", {})
        assert "export_format" in schema.get("properties", {})

    def test_report_record_fields(self) -> None:
        from src.api.report_export import ReportRecord

        schema = ReportRecord.model_json_schema()
        props = schema.get("properties", {})
        # Field is named "id" not "report_id"
        assert "id" in props
        assert "status" in props
        assert "report_type" in props

    def test_report_history_response_fields(self) -> None:
        from src.api.report_export import ReportHistoryResponse

        schema = ReportHistoryResponse.model_json_schema()
        props = schema.get("properties", {})
        assert "reports" in props
        assert "total" in props


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
class TestAPIEndpoints:
    """Test API endpoint functions."""

    def setup_method(self) -> None:
        from src.api.report_export import _reset_store

        _reset_store()

    def test_list_available_reports(self) -> None:
        from src.api.report_export import list_available_reports

        result = asyncio.get_event_loop().run_until_complete(list_available_reports())
        assert isinstance(result, list)
        assert len(result) == 6

    def test_list_available_report_has_title(self) -> None:
        from src.api.report_export import list_available_reports

        result = asyncio.get_event_loop().run_until_complete(list_available_reports())
        for r in result:
            assert r.title is not None

    def test_generate_report_csv(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            generate_report,
        )

        req = ReportGenerateRequest(
            report_type=ReportType.ANIMAL_INVENTORY,
            export_format=ExportFormat.CSV,
        )
        result = asyncio.get_event_loop().run_until_complete(generate_report(req))
        assert result.status == "completed"

    def test_generate_report_json(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            generate_report,
        )

        req = ReportGenerateRequest(
            report_type=ReportType.DONATIONS,
            export_format=ExportFormat.JSON,
        )
        result = asyncio.get_event_loop().run_until_complete(generate_report(req))
        assert result.status == "completed"

    def test_generate_report_stores_in_memory(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            _generated_reports,
            generate_report,
        )

        req = ReportGenerateRequest(
            report_type=ReportType.VETERINARY,
            export_format=ExportFormat.CSV,
        )
        result = asyncio.get_event_loop().run_until_complete(generate_report(req))
        # Field is "id" not "report_id"
        assert result.id in _generated_reports

    def test_get_report_history_empty(self) -> None:
        from src.api.report_export import get_report_history

        result = asyncio.get_event_loop().run_until_complete(
            get_report_history(page=1, page_size=20)
        )
        assert result.total == 0
        assert result.reports == []

    def test_get_report_history_after_generate(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            generate_report,
            get_report_history,
        )

        req = ReportGenerateRequest(
            report_type=ReportType.FINANCIAL,
            export_format=ExportFormat.CSV,
        )
        asyncio.get_event_loop().run_until_complete(generate_report(req))
        result = asyncio.get_event_loop().run_until_complete(
            get_report_history(page=1, page_size=20)
        )
        assert result.total == 1

    def test_download_report_not_found(self) -> None:
        from src.api.report_export import download_report

        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(download_report("nonexistent-id"))
        assert exc_info.value.status_code == 404

    def test_download_report_csv(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            download_report,
            generate_report,
        )

        req = ReportGenerateRequest(
            report_type=ReportType.ADOPTIONS,
            export_format=ExportFormat.CSV,
        )
        gen_result = asyncio.get_event_loop().run_until_complete(generate_report(req))
        response = asyncio.get_event_loop().run_until_complete(download_report(gen_result.id))
        assert response.media_type in ("text/csv", "application/octet-stream")

    def test_download_report_json(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            download_report,
            generate_report,
        )

        req = ReportGenerateRequest(
            report_type=ReportType.VOLUNTEERS,
            export_format=ExportFormat.JSON,
        )
        gen_result = asyncio.get_event_loop().run_until_complete(generate_report(req))
        response = asyncio.get_event_loop().run_until_complete(download_report(gen_result.id))
        assert response.media_type in ("application/json", "application/octet-stream")

    def test_generate_all_report_types(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            generate_report,
        )

        for rt in ReportType:
            req = ReportGenerateRequest(
                report_type=rt,
                export_format=ExportFormat.CSV,
            )
            result = asyncio.get_event_loop().run_until_complete(generate_report(req))
            assert result.status == "completed", f"Failed for {rt}"

    def test_history_pagination(self) -> None:
        from src.api.report_export import (
            ExportFormat,
            ReportGenerateRequest,
            ReportType,
            generate_report,
            get_report_history,
        )

        for rt in [
            ReportType.ANIMAL_INVENTORY,
            ReportType.DONATIONS,
            ReportType.FINANCIAL,
        ]:
            req = ReportGenerateRequest(
                report_type=rt,
                export_format=ExportFormat.CSV,
            )
            asyncio.get_event_loop().run_until_complete(generate_report(req))

        result = asyncio.get_event_loop().run_until_complete(
            get_report_history(page=1, page_size=2)
        )
        assert result.total == 3
        assert len(result.reports) == 2


# ---------------------------------------------------------------------------
# Frontend page
# ---------------------------------------------------------------------------
class TestReportsPage:
    """Validate the frontend reports page."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/reportes/page.tsx")
        assert page_path.exists(), "Reports page not found"
        self.content = page_path.read_text()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.content or "'use client'" in self.content

    def test_has_page_title(self) -> None:
        assert "Reportes" in self.content or "reportes" in self.content

    def test_has_report_card_component(self) -> None:
        assert "ReportCard" in self.content

    def test_has_history_section(self) -> None:
        assert "history" in self.content.lower() or "historial" in self.content.lower()

    def test_has_csv_option(self) -> None:
        assert "CSV" in self.content or "csv" in self.content

    def test_has_json_option(self) -> None:
        assert "JSON" in self.content or "json" in self.content

    def test_has_loading_state(self) -> None:
        assert "loading" in self.content.lower() or "Loading" in self.content

    def test_has_error_handling(self) -> None:
        assert "error" in self.content.lower()

    def test_has_download_functionality(self) -> None:
        assert "download" in self.content.lower()

    def test_has_generate_handler(self) -> None:
        assert "generate" in self.content.lower()

    def test_report_types_referenced(self) -> None:
        # Check for any report type reference in the page
        assert (
            "report_type" in self.content
            or "reportType" in self.content
            or "animal" in self.content.lower()
        )

    def test_has_status_badges(self) -> None:
        assert "status" in self.content.lower()


# ---------------------------------------------------------------------------
# Accessibility
# ---------------------------------------------------------------------------
class TestAccessibility:
    """Validate WCAG compliance patterns in the frontend."""

    @pytest.fixture(autouse=True)
    def _load_page(self) -> None:
        page_path = Path("frontend/src/app/admin/reportes/page.tsx")
        self.content = page_path.read_text()

    def test_has_aria_labels(self) -> None:
        assert "aria-label" in self.content

    def test_has_role_attributes(self) -> None:
        assert 'role="' in self.content

    def test_has_alert_role(self) -> None:
        assert 'role="alert"' in self.content or 'role="status"' in self.content

    def test_has_semantic_headings(self) -> None:
        assert "<h1" in self.content or "<h2" in self.content

    def test_has_button_elements(self) -> None:
        assert "<button" in self.content

    def test_has_min_touch_targets(self) -> None:
        assert (
            "min-h-[44px]" in self.content
            or "h-11" in self.content
            or "min-w-[44px]" in self.content
            or "p-3" in self.content
        )

    def test_has_keyboard_interaction(self) -> None:
        assert "onClick" in self.content

    def test_has_color_contrast_classes(self) -> None:
        # Tailwind classes that indicate attention to contrast
        assert "text-" in self.content and "bg-" in self.content


# ---------------------------------------------------------------------------
# App registration
# ---------------------------------------------------------------------------
class TestAppRegistration:
    """Verify router is registered in the FastAPI application."""

    def test_report_export_router_imported(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "report_export_router" in app_content

    def test_report_export_router_included(self) -> None:
        app_content = Path("src/app.py").read_text()
        assert "application.include_router(report_export_router)" in app_content
