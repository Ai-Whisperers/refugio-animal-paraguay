"""Tests for pre-adoption reading enforcement feature (RAP-628).

Covers:
    - Module structure and constants
    - Reading requirements data
    - Progress tracking
    - Completion verification
    - API endpoints
    - Frontend page structure and accessibility
"""

from datetime import UTC
from pathlib import Path

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Test: Module Structure
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify pre_adoption_reading module exports and structure."""

    def test_module_imports(self) -> None:
        from src.api import pre_adoption_reading

        assert hasattr(pre_adoption_reading, "router")

    def test_router_has_prefix(self) -> None:
        from src.api.pre_adoption_reading import router

        assert any(
            r.path.startswith("/api/adoption-reading") for r in router.routes if hasattr(r, "path")
        )

    def test_router_has_tag(self) -> None:
        from src.api.pre_adoption_reading import router

        assert "pre-adoption-reading" in router.tags

    def test_reading_category_enum_exists(self) -> None:
        from src.api.pre_adoption_reading import ReadingCategory

        assert hasattr(ReadingCategory, "RESPONSIBLE_OWNERSHIP")
        assert hasattr(ReadingCategory, "HEALTH_CARE")
        assert hasattr(ReadingCategory, "LEGAL_REQUIREMENTS")
        assert hasattr(ReadingCategory, "COMMITMENT")
        assert hasattr(ReadingCategory, "PREPARATION")

    def test_reading_status_enum_exists(self) -> None:
        from src.api.pre_adoption_reading import ReadingStatus

        assert hasattr(ReadingStatus, "NOT_STARTED")
        assert hasattr(ReadingStatus, "IN_PROGRESS")
        assert hasattr(ReadingStatus, "COMPLETED")


# ---------------------------------------------------------------------------
# Test: Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constants are properly defined."""

    def test_max_readings(self) -> None:
        from src.api.pre_adoption_reading import MAX_READINGS

        assert MAX_READINGS == 20

    def test_min_reading_time(self) -> None:
        from src.api.pre_adoption_reading import MIN_READING_TIME_SECONDS

        assert MIN_READING_TIME_SECONDS == 30

    def test_session_expiry_days(self) -> None:
        from src.api.pre_adoption_reading import SESSION_EXPIRY_DAYS

        assert SESSION_EXPIRY_DAYS == 30

    def test_reading_complete_threshold(self) -> None:
        from src.api.pre_adoption_reading import READING_COMPLETE_THRESHOLD

        assert READING_COMPLETE_THRESHOLD == 1.0

    def test_constants_are_positive(self) -> None:
        from src.api.pre_adoption_reading import (
            MAX_READINGS,
            MIN_READING_TIME_SECONDS,
            SESSION_EXPIRY_DAYS,
        )

        assert MAX_READINGS > 0
        assert MIN_READING_TIME_SECONDS > 0
        assert SESSION_EXPIRY_DAYS > 0


# ---------------------------------------------------------------------------
# Test: Required Readings Data
# ---------------------------------------------------------------------------


class TestRequiredReadings:
    """Verify reading requirements data integrity."""

    def test_readings_exist(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        assert len(REQUIRED_READINGS) > 0

    def test_all_readings_have_required_fields(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        required_fields = {
            "id",
            "title",
            "description",
            "category",
            "estimated_minutes",
            "content_url",
            "order",
            "required",
        }
        for reading in REQUIRED_READINGS:
            missing = required_fields - set(reading.keys())
            assert not missing, f"Reading {reading.get('id')} missing: {missing}"

    def test_reading_ids_unique(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        ids = [r["id"] for r in REQUIRED_READINGS]
        assert len(ids) == len(set(ids)), "Duplicate reading IDs found"

    def test_reading_orders_unique(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        orders = [r["order"] for r in REQUIRED_READINGS]
        assert len(orders) == len(set(orders)), "Duplicate reading orders"

    def test_all_readings_have_spanish_titles(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        for reading in REQUIRED_READINGS:
            assert len(reading["title"]) > 5, f"Title too short: {reading['id']}"

    def test_content_urls_start_with_slash(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        for reading in REQUIRED_READINGS:
            assert reading["content_url"].startswith("/"), f"URL must be relative: {reading['id']}"

    def test_estimated_minutes_reasonable(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        for reading in REQUIRED_READINGS:
            assert 1 <= reading["estimated_minutes"] <= 60, f"Time out of range: {reading['id']}"

    def test_five_required_readings(self) -> None:
        from src.api.pre_adoption_reading import REQUIRED_READINGS

        required = [r for r in REQUIRED_READINGS if r.get("required", True)]
        assert len(required) == 5

    def test_categories_cover_all_types(self) -> None:
        from src.api.pre_adoption_reading import (
            REQUIRED_READINGS,
            ReadingCategory,
        )

        categories = {r["category"] for r in REQUIRED_READINGS}
        expected = {
            ReadingCategory.RESPONSIBLE_OWNERSHIP,
            ReadingCategory.HEALTH_CARE,
            ReadingCategory.LEGAL_REQUIREMENTS,
            ReadingCategory.COMMITMENT,
            ReadingCategory.PREPARATION,
        }
        assert categories == expected


# ---------------------------------------------------------------------------
# Test: Schemas
# ---------------------------------------------------------------------------


class TestSchemas:
    """Verify Pydantic schema structure."""

    def test_reading_requirement_schema(self) -> None:
        from src.api.pre_adoption_reading import ReadingCategory, ReadingRequirement

        req = ReadingRequirement(
            id="test-reading",
            title="Test",
            description="Desc",
            category=ReadingCategory.HEALTH_CARE,
            estimated_minutes=5,
            content_url="/test",
            order=1,
            required=True,
        )
        assert req.id == "test-reading"

    def test_reading_progress_schema(self) -> None:
        from src.api.pre_adoption_reading import ReadingProgress

        p = ReadingProgress(reading_id="test-1")
        assert p.status == "not_started"
        assert p.time_spent_seconds == 0

    def test_reading_complete_request_validation(self) -> None:
        from src.api.pre_adoption_reading import ReadingCompleteRequest

        req = ReadingCompleteRequest(time_spent_seconds=60, session_id="abc")
        assert req.time_spent_seconds == 60

    def test_reading_verification_schema(self) -> None:
        from datetime import datetime

        from src.api.pre_adoption_reading import ReadingVerification

        v = ReadingVerification(
            eligible=True,
            completed_count=5,
            required_count=5,
            missing_readings=[],
            verified_at=datetime.now(UTC),
        )
        assert v.eligible is True

    def test_progress_summary_schema(self) -> None:
        from src.api.pre_adoption_reading import ReadingProgressSummary

        s = ReadingProgressSummary(
            total_required=5,
            completed=3,
            completion_percentage=60.0,
            all_required_complete=False,
            readings=[],
            session_id="test",
        )
        assert s.completion_percentage == 60.0


# ---------------------------------------------------------------------------
# Test: Helper Functions
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    """Test internal helper functions."""

    def setup_method(self) -> None:
        from src.api.pre_adoption_reading import _reset_store

        _reset_store()

    def test_get_requirements_returns_list(self) -> None:
        from src.api.pre_adoption_reading import _get_requirements

        reqs = _get_requirements()
        assert isinstance(reqs, list)
        assert len(reqs) > 0

    def test_get_required_ids(self) -> None:
        from src.api.pre_adoption_reading import _get_required_ids

        ids = _get_required_ids()
        assert isinstance(ids, set)
        assert len(ids) == 5

    def test_get_session_progress_creates_new(self) -> None:
        from src.api.pre_adoption_reading import _get_session_progress

        progress = _get_session_progress("new-session")
        assert isinstance(progress, dict)
        assert len(progress) == 0

    def test_build_progress_summary_empty(self) -> None:
        from src.api.pre_adoption_reading import _build_progress_summary

        summary = _build_progress_summary("new-session")
        assert summary.total_required == 5
        assert summary.completed == 0
        assert summary.completion_percentage == 0.0
        assert summary.all_required_complete is False

    def test_build_progress_summary_partial(self) -> None:
        from datetime import datetime

        from src.api.pre_adoption_reading import (
            ReadingProgress,
            ReadingStatus,
            _build_progress_summary,
            _get_session_progress,
        )

        progress = _get_session_progress("test-session")
        progress["responsible-ownership-basics"] = ReadingProgress(
            reading_id="responsible-ownership-basics",
            status=ReadingStatus.COMPLETED,
            completed_at=datetime.now(UTC),
            time_spent_seconds=60,
        )
        summary = _build_progress_summary("test-session")
        assert summary.completed == 1
        assert summary.completion_percentage == 20.0

    def test_build_progress_summary_all_complete(self) -> None:
        from datetime import datetime

        from src.api.pre_adoption_reading import (
            REQUIRED_READINGS,
            ReadingProgress,
            ReadingStatus,
            _build_progress_summary,
            _get_session_progress,
        )

        progress = _get_session_progress("done-session")
        for r in REQUIRED_READINGS:
            progress[r["id"]] = ReadingProgress(
                reading_id=r["id"],
                status=ReadingStatus.COMPLETED,
                completed_at=datetime.now(UTC),
                time_spent_seconds=60,
            )
        summary = _build_progress_summary("done-session")
        assert summary.all_required_complete is True
        assert summary.completion_percentage == 100.0

    def test_reset_store_clears_data(self) -> None:
        from src.api.pre_adoption_reading import (
            _get_session_progress,
            _reading_sessions,
            _reset_store,
        )

        _get_session_progress("session-1")
        assert len(_reading_sessions) > 0
        _reset_store()
        assert len(_reading_sessions) == 0


# ---------------------------------------------------------------------------
# Test: API Endpoints
# ---------------------------------------------------------------------------


class TestAPIEndpoints:
    """Test API endpoint behavior."""

    def test_requirements_endpoint_exists(self) -> None:
        from src.api.pre_adoption_reading import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert "/requirements" in paths or any("/requirements" in p for p in paths)

    def test_complete_endpoint_exists(self) -> None:
        from src.api.pre_adoption_reading import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert any("complete" in p for p in paths)

    def test_progress_endpoint_exists(self) -> None:
        from src.api.pre_adoption_reading import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert "/progress" in paths or any("/progress" in p for p in paths)

    def test_verify_endpoint_exists(self) -> None:
        from src.api.pre_adoption_reading import router

        paths = [r.path for r in router.routes if hasattr(r, "path")]
        assert "/verify" in paths or any("/verify" in p for p in paths)

    @pytest.mark.asyncio
    async def test_list_requirements(self) -> None:
        from src.api.pre_adoption_reading import list_reading_requirements

        result = await list_reading_requirements(category=None)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_list_requirements_filtered(self) -> None:
        from src.api.pre_adoption_reading import (
            ReadingCategory,
            list_reading_requirements,
        )

        result = await list_reading_requirements(category=ReadingCategory.HEALTH_CARE)
        assert len(result) == 1
        assert result[0].category == ReadingCategory.HEALTH_CARE

    @pytest.mark.asyncio
    async def test_complete_reading_success(self) -> None:
        from src.api.pre_adoption_reading import (
            ReadingCompleteRequest,
            _reset_store,
            complete_reading,
        )

        _reset_store()
        req = ReadingCompleteRequest(time_spent_seconds=60, session_id="test-session")
        result = await complete_reading("responsible-ownership-basics", req)
        assert result.status == "completed"
        assert result.progress_summary.completed == 1

    @pytest.mark.asyncio
    async def test_complete_reading_not_found(self) -> None:
        from src.api.pre_adoption_reading import (
            ReadingCompleteRequest,
            complete_reading,
        )

        req = ReadingCompleteRequest(time_spent_seconds=60, session_id="test-session")
        with pytest.raises(HTTPException):
            await complete_reading("nonexistent-reading", req)

    @pytest.mark.asyncio
    async def test_complete_reading_too_fast(self) -> None:
        from src.api.pre_adoption_reading import (
            ReadingCompleteRequest,
            complete_reading,
        )

        req = ReadingCompleteRequest(time_spent_seconds=5, session_id="test-session")
        with pytest.raises(HTTPException):
            await complete_reading("responsible-ownership-basics", req)

    @pytest.mark.asyncio
    async def test_complete_reading_idempotent(self) -> None:
        from src.api.pre_adoption_reading import (
            ReadingCompleteRequest,
            _reset_store,
            complete_reading,
        )

        _reset_store()
        req = ReadingCompleteRequest(time_spent_seconds=60, session_id="test-session")
        r1 = await complete_reading("responsible-ownership-basics", req)
        r2 = await complete_reading("responsible-ownership-basics", req)
        assert r1.status == "completed"
        assert r2.status == "completed"
        assert r2.progress_summary.completed == 1

    @pytest.mark.asyncio
    async def test_get_progress(self) -> None:
        from src.api.pre_adoption_reading import (
            _reset_store,
            get_reading_progress,
        )

        _reset_store()
        result = await get_reading_progress(session_id="new-session")
        assert result.total_required == 5
        assert result.completed == 0

    @pytest.mark.asyncio
    async def test_verify_not_eligible(self) -> None:
        from src.api.pre_adoption_reading import (
            _reset_store,
            verify_reading_completion,
        )

        _reset_store()
        result = await verify_reading_completion(session_id="new-session")
        assert result.eligible is False
        assert len(result.missing_readings) == 5

    @pytest.mark.asyncio
    async def test_verify_eligible_after_all_complete(self) -> None:
        from src.api.pre_adoption_reading import (
            REQUIRED_READINGS,
            ReadingCompleteRequest,
            _reset_store,
            complete_reading,
            verify_reading_completion,
        )

        _reset_store()
        session = "full-session"
        for r in REQUIRED_READINGS:
            req = ReadingCompleteRequest(time_spent_seconds=60, session_id=session)
            await complete_reading(r["id"], req)
        result = await verify_reading_completion(session_id=session)
        assert result.eligible is True
        assert len(result.missing_readings) == 0


# ---------------------------------------------------------------------------
# Test: Frontend Page Structure
# ---------------------------------------------------------------------------


class TestReadingPage:
    """Verify frontend page structure."""

    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/animals/[id]/reading/page.tsx")
        assert page_path.exists(), f"Page not found: {page_path}"
        return page_path.read_text()

    def test_page_is_client_component(self, page_content: str) -> None:
        assert '"use client"' in page_content

    def test_page_has_progress_bar(self, page_content: str) -> None:
        assert "ProgressBar" in page_content
        assert "progressbar" in page_content

    def test_page_has_reading_cards(self, page_content: str) -> None:
        assert "ReadingCard" in page_content

    def test_page_has_breadcrumb(self, page_content: str) -> None:
        assert "Breadcrumb" in page_content.lower() or "breadcrumb" in page_content.lower()

    def test_page_has_loading_skeleton(self, page_content: str) -> None:
        assert "LoadingSkeleton" in page_content

    def test_page_has_error_handling(self, page_content: str) -> None:
        assert "error" in page_content.lower()
        assert 'role="alert"' in page_content

    def test_page_has_eligible_banner(self, page_content: str) -> None:
        assert "EligibleBanner" in page_content

    def test_page_fetches_requirements(self, page_content: str) -> None:
        assert "adoption-reading/requirements" in page_content

    def test_page_fetches_progress(self, page_content: str) -> None:
        assert "adoption-reading/progress" in page_content

    def test_page_has_mark_complete(self, page_content: str) -> None:
        assert "handleMarkComplete" in page_content or "onMarkComplete" in page_content

    def test_page_links_to_apply(self, page_content: str) -> None:
        assert "/apply" in page_content

    def test_page_links_to_content(self, page_content: str) -> None:
        assert "content_url" in page_content

    def test_page_has_session_management(self, page_content: str) -> None:
        assert "sessionId" in page_content or "session_id" in page_content

    def test_page_has_spanish_content(self, page_content: str) -> None:
        assert "Lecturas" in page_content
        assert "adopción" in page_content or "adopcion" in page_content

    def test_page_has_category_icons(self, page_content: str) -> None:
        assert "Heart" in page_content
        assert "Shield" in page_content
        assert "Scale" in page_content

    def test_page_has_min_reading_time(self, page_content: str) -> None:
        assert "MIN_READING_SECONDS" in page_content


# ---------------------------------------------------------------------------
# Test: Accessibility
# ---------------------------------------------------------------------------


class TestAccessibility:
    """Verify accessibility features."""

    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/animals/[id]/reading/page.tsx")
        return page_path.read_text()

    def test_has_aria_labels(self, page_content: str) -> None:
        assert "aria-label" in page_content

    def test_has_aria_busy(self, page_content: str) -> None:
        assert "aria-busy" in page_content

    def test_has_role_progressbar(self, page_content: str) -> None:
        assert 'role="progressbar"' in page_content

    def test_has_role_alert(self, page_content: str) -> None:
        assert 'role="alert"' in page_content

    def test_has_role_list(self, page_content: str) -> None:
        assert 'role="list"' in page_content

    def test_has_aria_current(self, page_content: str) -> None:
        assert "aria-current" in page_content

    def test_has_min_touch_targets(self, page_content: str) -> None:
        assert "min-h-[44px]" in page_content

    def test_has_aria_valuenow(self, page_content: str) -> None:
        assert "aria-valuenow" in page_content

    def test_has_aria_hidden_for_icons(self, page_content: str) -> None:
        assert 'aria-hidden="true"' in page_content


# ---------------------------------------------------------------------------
# Test: App Registration
# ---------------------------------------------------------------------------


class TestAppRegistration:
    """Verify router is registered in app.py."""

    def test_router_imported_in_app(self) -> None:
        content = Path("src/app.py").read_text()
        assert "pre_adoption_reading" in content

    def test_router_included_in_app(self) -> None:
        content = Path("src/app.py").read_text()
        assert "pre_adoption_reading_router" in content
