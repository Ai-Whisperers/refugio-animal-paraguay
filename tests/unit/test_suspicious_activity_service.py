"""Unit tests for the suspicious activity detection service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from src.services.suspicious_activity_service import (
    BULK_DELETE_THRESHOLD,
    BULK_EXPORT_THRESHOLD,
    DETECTION_WINDOW_MINUTES,
    GDPR_ERASURE_THRESHOLD,
    HIGH_FREQUENCY_THRESHOLD,
    AlertSeverity,
    AlertType,
    SuspiciousActivityAlert,
    SuspiciousActivityReport,
    detect_suspicious_activity,
)

USER_A = UUID("aaaaaaaa-0000-0000-0000-000000000001")
USER_B = UUID("bbbbbbbb-0000-0000-0000-000000000002")


def _make_row(user_id: UUID, cnt: int) -> MagicMock:
    row = MagicMock()
    row.user_id = user_id
    row.cnt = cnt
    return row


def _agg_result(rows: list) -> MagicMock:
    """Result for aggregate queries (rows with .user_id and .cnt attributes)."""
    r = MagicMock()
    r.fetchall.return_value = rows
    return r


def _scalar_result(values: list[str]) -> MagicMock:
    """Result for _recent_resource_types (distinct resource_type strings)."""
    r = MagicMock()
    r.fetchall.return_value = [(v,) for v in values]
    return r


def _make_db(
    *,
    delete_rows: list | None = None,
    export_rows: list | None = None,
    gdpr_rows: list | None = None,
    freq_rows: list | None = None,
    resource_types: list[str] | None = None,
) -> AsyncMock:
    """Build a mock AsyncSession with configurable query results.

    The execute call order matches the service implementation:
      delete_query → [resource_types per delete row] →
      export_query → [resource_types per export row] →
      gdpr_query   → (no resource sub-query) →
      freq_query   → [resource_types per freq row]
    """
    db = AsyncMock()
    rt = resource_types or []
    d_rows = delete_rows or []
    e_rows = export_rows or []
    g_rows = gdpr_rows or []
    f_rows = freq_rows or []

    results: list[MagicMock] = []

    # 1. delete aggregate
    results.append(_agg_result(d_rows))
    # resource_types for each delete row
    for _ in d_rows:
        results.append(_scalar_result(rt))

    # 2. export aggregate
    results.append(_agg_result(e_rows))
    # resource_types for each export row
    for _ in e_rows:
        results.append(_scalar_result(rt))

    # 3. gdpr aggregate (no resource sub-query)
    results.append(_agg_result(g_rows))

    # 4. freq aggregate
    results.append(_agg_result(f_rows))
    # resource_types for each freq row not already flagged for bulk_delete
    delete_user_ids = {r.user_id for r in d_rows}
    for row in f_rows:
        if row.user_id not in delete_user_ids:
            results.append(_scalar_result(rt))

    db.execute = AsyncMock(side_effect=results)
    return db


# --- Basic empty result ---


@pytest.mark.asyncio
async def test_no_alerts_when_no_anomalies() -> None:
    db = _make_db()
    report = await detect_suspicious_activity(db)

    assert isinstance(report, SuspiciousActivityReport)
    assert report.alert_count == 0
    assert report.alerts == []
    assert report.window_minutes == DETECTION_WINDOW_MINUTES


# --- Bulk delete ---


@pytest.mark.asyncio
async def test_bulk_delete_emits_high_severity_alert() -> None:
    db = _make_db(
        delete_rows=[_make_row(USER_A, BULK_DELETE_THRESHOLD)],
        resource_types=["animal", "donor"],
    )
    report = await detect_suspicious_activity(db)

    assert report.alert_count == 1
    alert = report.alerts[0]
    assert alert.alert_type == AlertType.BULK_DELETE
    assert alert.severity == AlertSeverity.HIGH
    assert alert.user_id == USER_A
    assert alert.count == BULK_DELETE_THRESHOLD
    assert "animal" in alert.recent_resource_types or "donor" in alert.recent_resource_types


@pytest.mark.asyncio
async def test_bulk_delete_description_contains_count() -> None:
    db = _make_db(delete_rows=[_make_row(USER_A, 15)])
    report = await detect_suspicious_activity(db)

    assert "15" in report.alerts[0].description


# --- Bulk export ---


@pytest.mark.asyncio
async def test_bulk_export_emits_medium_severity_alert() -> None:
    db = _make_db(export_rows=[_make_row(USER_B, BULK_EXPORT_THRESHOLD)])
    report = await detect_suspicious_activity(db)

    alert = next(a for a in report.alerts if a.alert_type == AlertType.BULK_EXPORT)
    assert alert.severity == AlertSeverity.MEDIUM
    assert alert.user_id == USER_B


# --- GDPR erasure burst ---


@pytest.mark.asyncio
async def test_gdpr_erasure_burst_emits_high_severity_alert() -> None:
    db = _make_db(gdpr_rows=[_make_row(USER_A, GDPR_ERASURE_THRESHOLD)])
    report = await detect_suspicious_activity(db)

    alert = next(
        a for a in report.alerts if a.alert_type == AlertType.GDPR_ERASURE_BURST
    )
    assert alert.severity == AlertSeverity.HIGH
    assert "Manual review" in alert.description


# --- High frequency activity ---


@pytest.mark.asyncio
async def test_high_frequency_activity_emits_low_severity_alert() -> None:
    db = _make_db(freq_rows=[_make_row(USER_B, HIGH_FREQUENCY_THRESHOLD)])
    report = await detect_suspicious_activity(db)

    alert = next(
        a for a in report.alerts if a.alert_type == AlertType.HIGH_FREQUENCY_ACTIVITY
    )
    assert alert.severity == AlertSeverity.LOW


@pytest.mark.asyncio
async def test_high_frequency_not_emitted_if_already_flagged_for_bulk_delete() -> None:
    """A user who already has a BULK_DELETE alert should not also get HIGH_FREQUENCY."""
    db = _make_db(
        delete_rows=[_make_row(USER_A, BULK_DELETE_THRESHOLD)],
        freq_rows=[_make_row(USER_A, HIGH_FREQUENCY_THRESHOLD)],
    )
    report = await detect_suspicious_activity(db)

    types = [a.alert_type for a in report.alerts]
    assert AlertType.HIGH_FREQUENCY_ACTIVITY not in types


# --- Multiple alerts ---


@pytest.mark.asyncio
async def test_multiple_users_generate_multiple_alerts() -> None:
    db = _make_db(
        delete_rows=[_make_row(USER_A, BULK_DELETE_THRESHOLD)],
        export_rows=[_make_row(USER_B, BULK_EXPORT_THRESHOLD)],
    )
    report = await detect_suspicious_activity(db)

    assert report.alert_count == 2
    user_ids = {a.user_id for a in report.alerts}
    assert USER_A in user_ids
    assert USER_B in user_ids


# --- Window parameter ---


@pytest.mark.asyncio
async def test_custom_window_minutes_is_reflected_in_report() -> None:
    db = _make_db()
    report = await detect_suspicious_activity(db, window_minutes=30)

    assert report.window_minutes == 30


# --- Report metadata ---


@pytest.mark.asyncio
async def test_report_checked_at_is_recent() -> None:
    db = _make_db()
    before = datetime.now(UTC)
    report = await detect_suspicious_activity(db)
    after = datetime.now(UTC)

    assert before <= report.checked_at <= after
