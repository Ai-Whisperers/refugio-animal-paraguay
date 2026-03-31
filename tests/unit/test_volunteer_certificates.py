"""Unit tests for volunteer certificates API (RAP-198).

Tests schemas, helpers, and milestone logic without a live database.
"""

from datetime import UTC, datetime
from uuid import uuid4

from src.api.volunteer_certificates import (
    CertificateIssuedBy,
    CertificateListResponse,
    CertificateResponse,
    IssueCertificateRequest,
    _eligible_milestones,
)
from src.db.models.volunteer_certificate import CERTIFICATE_MILESTONES

# ---------------------------------------------------------------------------
# CERTIFICATE_MILESTONES constant
# ---------------------------------------------------------------------------


class TestCertificateMilestones:
    def test_milestones_non_empty(self) -> None:
        assert len(CERTIFICATE_MILESTONES) > 0

    def test_milestones_all_positive(self) -> None:
        assert all(m > 0 for m in CERTIFICATE_MILESTONES)

    def test_milestones_contains_50(self) -> None:
        assert 50 in CERTIFICATE_MILESTONES

    def test_milestones_contains_100(self) -> None:
        assert 100 in CERTIFICATE_MILESTONES

    def test_milestones_contains_500(self) -> None:
        assert 500 in CERTIFICATE_MILESTONES


# ---------------------------------------------------------------------------
# _eligible_milestones helper
# ---------------------------------------------------------------------------


class TestEligibleMilestones:
    def test_no_hours_no_milestones(self) -> None:
        assert _eligible_milestones(0.0, set()) == []

    def test_exactly_at_milestone(self) -> None:
        result = _eligible_milestones(50.0, set())
        assert 50 in result

    def test_below_lowest_milestone(self) -> None:
        assert _eligible_milestones(10.0, set()) == []

    def test_already_issued_excluded(self) -> None:
        result = _eligible_milestones(100.0, {50})
        assert 50 not in result
        assert 100 in result

    def test_all_issued_returns_empty(self) -> None:
        all_milestones = set(CERTIFICATE_MILESTONES)
        max_hours = float(max(CERTIFICATE_MILESTONES))
        result = _eligible_milestones(max_hours, all_milestones)
        assert result == []

    def test_result_sorted_ascending(self) -> None:
        result = _eligible_milestones(1000.0, set())
        assert result == sorted(result)

    def test_fractional_hours_below_milestone(self) -> None:
        # 49.9 is below 50 milestone
        assert _eligible_milestones(49.9, set()) == []

    def test_fractional_hours_above_milestone(self) -> None:
        # 50.1 is above 50 milestone
        result = _eligible_milestones(50.1, set())
        assert 50 in result


# ---------------------------------------------------------------------------
# IssueCertificateRequest schema
# ---------------------------------------------------------------------------


class TestIssueCertificateRequest:
    def test_valid_request(self) -> None:
        req = IssueCertificateRequest(milestone_hours=50)
        assert req.milestone_hours == 50
        assert req.notes is None
        assert req.send_thank_you is True

    def test_with_notes(self) -> None:
        req = IssueCertificateRequest(milestone_hours=100, notes="Great work!")
        assert req.notes == "Great work!"

    def test_send_thank_you_false(self) -> None:
        req = IssueCertificateRequest(milestone_hours=50, send_thank_you=False)
        assert req.send_thank_you is False


# ---------------------------------------------------------------------------
# CertificateResponse schema
# ---------------------------------------------------------------------------


class TestCertificateResponse:
    def _make_response(self, **overrides) -> dict:
        now = datetime.now(UTC)
        data = {
            "id": uuid4(),
            "volunteer_id": uuid4(),
            "milestone_hours": 100,
            "issued_at": now,
            "issued_by": None,
            "thank_you_sent": False,
            "thank_you_sent_at": None,
            "notes": None,
        }
        data.update(overrides)
        return data

    def test_valid_response(self) -> None:
        resp = CertificateResponse(**self._make_response())
        assert resp.milestone_hours == 100
        assert resp.thank_you_sent is False

    def test_with_issuer(self) -> None:
        issuer = CertificateIssuedBy(user_id=uuid4(), full_name="Staff Member")
        resp = CertificateResponse(**self._make_response(issued_by=issuer))
        assert resp.issued_by is not None
        assert resp.issued_by.full_name == "Staff Member"

    def test_with_thank_you_sent(self) -> None:
        now = datetime.now(UTC)
        resp = CertificateResponse(
            **self._make_response(thank_you_sent=True, thank_you_sent_at=now)
        )
        assert resp.thank_you_sent is True
        assert resp.thank_you_sent_at is not None


# ---------------------------------------------------------------------------
# CertificateListResponse schema
# ---------------------------------------------------------------------------


class TestCertificateListResponse:
    def test_empty_list(self) -> None:
        resp = CertificateListResponse(
            volunteer_id=uuid4(),
            total_hours_logged=0.0,
            certificates=[],
            eligible_milestones=[],
        )
        assert resp.certificates == []
        assert resp.eligible_milestones == []

    def test_with_eligible_milestones(self) -> None:
        resp = CertificateListResponse(
            volunteer_id=uuid4(),
            total_hours_logged=120.0,
            certificates=[],
            eligible_milestones=[50, 100],
        )
        assert resp.eligible_milestones == [50, 100]
        assert resp.total_hours_logged == 120.0
