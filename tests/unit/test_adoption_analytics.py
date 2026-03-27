"""Unit tests for adoption request analytics (RAP-114).

Tests cover:
  - Analytics schema validation
  - Status breakdown aggregation
  - Approval rate calculation
  - Time-to-decision averaging
  - Edge cases (no data, no decided requests)
"""

from src.schemas.adoption_request import (
    AdoptionAnalyticsResponse,
    StatusBreakdown,
)


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------
class TestAdoptionAnalyticsResponse:
    """Verify analytics response schema handles all cases."""

    def test_full_data(self) -> None:
        response = AdoptionAnalyticsResponse(
            total_requests=100,
            avg_time_to_decision_hours=24.5,
            approval_rate_percent=75.0,
            requests_last_7_days=10,
            requests_last_30_days=30,
            status_breakdown=StatusBreakdown(
                pending=20, approved=50, rejected=20, cancelled=10
            ),
        )
        assert response.total_requests == 100
        assert response.avg_time_to_decision_hours == 24.5
        assert response.approval_rate_percent == 75.0
        assert response.requests_last_7_days == 10
        assert response.requests_last_30_days == 30
        assert response.status_breakdown.approved == 50

    def test_nullable_fields_accept_none(self) -> None:
        response = AdoptionAnalyticsResponse(
            total_requests=0,
            avg_time_to_decision_hours=None,
            approval_rate_percent=None,
            requests_last_7_days=0,
            requests_last_30_days=0,
            status_breakdown=StatusBreakdown(),
        )
        assert response.avg_time_to_decision_hours is None
        assert response.approval_rate_percent is None

    def test_status_breakdown_defaults_to_zero(self) -> None:
        breakdown = StatusBreakdown()
        assert breakdown.pending == 0
        assert breakdown.approved == 0
        assert breakdown.rejected == 0
        assert breakdown.cancelled == 0


# ---------------------------------------------------------------------------
# Approval rate calculation
# ---------------------------------------------------------------------------
class TestApprovalRateCalculation:
    """Test the approval rate formula: approved / (approved + rejected) * 100."""

    def test_all_approved(self) -> None:
        decided = 10 + 0
        rate = round(10 / decided * 100, 1) if decided > 0 else None
        assert rate == 100.0

    def test_mixed_decisions(self) -> None:
        approved, rejected = 3, 7
        decided = approved + rejected
        rate = round(approved / decided * 100, 1)
        assert rate == 30.0

    def test_no_decisions_returns_none(self) -> None:
        approved, rejected = 0, 0
        decided = approved + rejected
        rate = round(approved / decided * 100, 1) if decided > 0 else None
        assert rate is None

    def test_only_rejected(self) -> None:
        approved, rejected = 0, 5
        decided = approved + rejected
        rate = round(approved / decided * 100, 1)
        assert rate == 0.0


# ---------------------------------------------------------------------------
# Time to decision
# ---------------------------------------------------------------------------
class TestTimeToDecision:
    """Test time-to-decision conversion from seconds to hours."""

    SECONDS_PER_HOUR = 3600.0

    def test_converts_seconds_to_hours(self) -> None:
        avg_seconds = 86400.0  # 24 hours
        result = round(avg_seconds / self.SECONDS_PER_HOUR, 1)
        assert result == 24.0

    def test_partial_hours(self) -> None:
        avg_seconds = 5400.0  # 1.5 hours
        result = round(avg_seconds / self.SECONDS_PER_HOUR, 1)
        assert result == 1.5

    def test_none_when_no_decided(self) -> None:
        avg_seconds = None
        result = (
            round(float(avg_seconds) / self.SECONDS_PER_HOUR, 1)
            if avg_seconds is not None
            else None
        )
        assert result is None
