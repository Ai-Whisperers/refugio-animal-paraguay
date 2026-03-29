"""Unit tests for the capacity alerts service functions (RAP-253)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.operational_metrics_service import (
    DEFAULT_CRITICAL_THRESHOLD_PCT,
    DEFAULT_SHELTER_CAPACITY,
    DEFAULT_WARNING_THRESHOLD_PCT,
    MAX_THRESHOLD_PCT,
    MIN_THRESHOLD_PCT,
    CapacityAlert,
    CapacityAlertSeverity,
    CapacityAlertsResult,
    OccupancyMetrics,
    _build_capacity_alerts,
    get_capacity_alerts,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_db_with_population(total: int) -> AsyncMock:
    """Return a mock db that returns a population row summing to `total`."""
    db = AsyncMock()

    pop_row = MagicMock()
    # Distribute total across status fields (all in 'available' for simplicity)
    pop_row.intake = 0
    pop_row.quarantine = 0
    pop_row.available = total
    pop_row.foster = 0
    pop_row.under_treatment = 0
    pop_row.adopted = 0
    pop_row.deceased = 0

    pop_result = MagicMock()
    pop_result.one.return_value = pop_row
    db.execute = AsyncMock(return_value=pop_result)
    return db


# ---------------------------------------------------------------------------
# CapacityAlertSeverity constants
# ---------------------------------------------------------------------------


class TestCapacityAlertSeverity:
    def test_critical_value(self) -> None:
        assert CapacityAlertSeverity.CRITICAL == "critical"

    def test_warning_value(self) -> None:
        assert CapacityAlertSeverity.WARNING == "warning"

    def test_ok_value(self) -> None:
        assert CapacityAlertSeverity.OK == "ok"


# ---------------------------------------------------------------------------
# Default thresholds
# ---------------------------------------------------------------------------


class TestDefaultThresholds:
    def test_warning_threshold_default(self) -> None:
        assert DEFAULT_WARNING_THRESHOLD_PCT == 70.0

    def test_critical_threshold_default(self) -> None:
        assert DEFAULT_CRITICAL_THRESHOLD_PCT == 85.0

    def test_min_threshold_is_positive(self) -> None:
        assert MIN_THRESHOLD_PCT > 0

    def test_max_threshold_is_100(self) -> None:
        assert MAX_THRESHOLD_PCT == 100.0


# ---------------------------------------------------------------------------
# _build_capacity_alerts
# ---------------------------------------------------------------------------


class TestBuildCapacityAlerts:
    def _occupancy(self, current: int, capacity: int) -> OccupancyMetrics:
        return OccupancyMetrics(current_count=current, capacity=capacity)

    def test_no_alerts_below_warning(self) -> None:
        occupancy = self._occupancy(100, 200)  # 50% — below warning
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert alerts == []

    def test_warning_alert_at_warning_threshold(self) -> None:
        occupancy = self._occupancy(140, 200)  # 70% — exactly at warning
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert len(alerts) == 1
        assert alerts[0].severity == CapacityAlertSeverity.WARNING

    def test_warning_alert_above_warning_below_critical(self) -> None:
        occupancy = self._occupancy(160, 200)  # 80% — between warning and critical
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert len(alerts) == 1
        assert alerts[0].severity == CapacityAlertSeverity.WARNING

    def test_critical_alert_at_critical_threshold(self) -> None:
        occupancy = self._occupancy(170, 200)  # 85% — exactly at critical
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert len(alerts) == 1
        assert alerts[0].severity == CapacityAlertSeverity.CRITICAL

    def test_critical_alert_above_critical_threshold(self) -> None:
        occupancy = self._occupancy(190, 200)  # 95%
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert len(alerts) == 1
        assert alerts[0].severity == CapacityAlertSeverity.CRITICAL

    def test_alert_includes_occupancy_rate(self) -> None:
        occupancy = self._occupancy(170, 200)  # 85%
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert alerts[0].occupancy_rate_pct == 85.0

    def test_alert_includes_title(self) -> None:
        occupancy = self._occupancy(170, 200)
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert alerts[0].title

    def test_alert_includes_message(self) -> None:
        occupancy = self._occupancy(170, 200)
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert alerts[0].message

    def test_alert_includes_recommended_action(self) -> None:
        occupancy = self._occupancy(170, 200)
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert alerts[0].recommended_action

    def test_custom_thresholds_respected(self) -> None:
        occupancy = self._occupancy(60, 200)  # 30%
        # With custom warning at 20%, should trigger a warning
        alerts = _build_capacity_alerts(occupancy, 20.0, 90.0)
        assert len(alerts) == 1
        assert alerts[0].severity == CapacityAlertSeverity.WARNING

    def test_zero_capacity_returns_no_alerts(self) -> None:
        # Edge case: capacity=0 → rate=0, no alerts
        occupancy = OccupancyMetrics(current_count=0, capacity=0)
        alerts = _build_capacity_alerts(occupancy, 70.0, 85.0)
        assert alerts == []


# ---------------------------------------------------------------------------
# CapacityAlert
# ---------------------------------------------------------------------------


class TestCapacityAlert:
    def test_all_fields_stored(self) -> None:
        alert = CapacityAlert(
            severity="critical",
            title="Test",
            message="msg",
            occupancy_rate_pct=90.0,
            recommended_action="act",
        )
        assert alert.severity == "critical"
        assert alert.title == "Test"
        assert alert.message == "msg"
        assert alert.occupancy_rate_pct == 90.0
        assert alert.recommended_action == "act"


# ---------------------------------------------------------------------------
# get_capacity_alerts
# ---------------------------------------------------------------------------


class TestGetCapacityAlerts:
    @pytest.mark.asyncio
    async def test_returns_capacity_alerts_result(self) -> None:
        db = _make_db_with_population(100)
        result = await get_capacity_alerts(db, capacity=200)
        assert isinstance(result, CapacityAlertsResult)

    @pytest.mark.asyncio
    async def test_ok_status_below_warning(self) -> None:
        db = _make_db_with_population(100)  # 50% of 200
        result = await get_capacity_alerts(db, capacity=200)
        assert result.status == CapacityAlertSeverity.OK
        assert result.alerts == []

    @pytest.mark.asyncio
    async def test_warning_status_at_warning_threshold(self) -> None:
        db = _make_db_with_population(140)  # 70% of 200
        result = await get_capacity_alerts(db, capacity=200)
        assert result.status == CapacityAlertSeverity.WARNING
        assert len(result.alerts) == 1

    @pytest.mark.asyncio
    async def test_critical_status_at_critical_threshold(self) -> None:
        db = _make_db_with_population(170)  # 85% of 200
        result = await get_capacity_alerts(db, capacity=200)
        assert result.status == CapacityAlertSeverity.CRITICAL
        assert len(result.alerts) == 1

    @pytest.mark.asyncio
    async def test_result_stores_current_count(self) -> None:
        db = _make_db_with_population(80)
        result = await get_capacity_alerts(db, capacity=200)
        assert result.current_count == 80

    @pytest.mark.asyncio
    async def test_result_stores_capacity(self) -> None:
        db = _make_db_with_population(80)
        result = await get_capacity_alerts(db, capacity=150)
        assert result.capacity == 150

    @pytest.mark.asyncio
    async def test_result_stores_thresholds(self) -> None:
        db = _make_db_with_population(80)
        result = await get_capacity_alerts(db, warning_threshold_pct=60.0, critical_threshold_pct=80.0)
        assert result.warning_threshold_pct == 60.0
        assert result.critical_threshold_pct == 80.0

    @pytest.mark.asyncio
    async def test_generated_at_is_iso(self) -> None:
        db = _make_db_with_population(80)
        result = await get_capacity_alerts(db)
        assert "T" in result.generated_at

    @pytest.mark.asyncio
    async def test_uses_default_shelter_capacity(self) -> None:
        db = _make_db_with_population(80)
        result = await get_capacity_alerts(db)
        assert result.capacity == DEFAULT_SHELTER_CAPACITY
