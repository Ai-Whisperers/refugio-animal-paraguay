"""Unit tests for donors API list/export logic.

Tests the _build_donor_list_query helper and schema validation
without touching the database.
"""

from src.api.donors import _ALLOWED_SORT_FIELDS, _build_donor_list_query
from src.schemas.donation import DonorListResponse, DonorResponse

# ---------------------------------------------------------------------------
# _build_donor_list_query
# ---------------------------------------------------------------------------


class TestBuildDonorListQuery:
    """Tests for the query builder helper function."""

    def test_returns_select_statement_with_defaults(self) -> None:
        stmt = _build_donor_list_query(
            search=None,
            country=None,
            has_gdpr_consent=None,
            sort_by="created_at",
            sort_order="desc",
        )
        compiled = str(stmt.compile())
        assert "donors" in compiled

    def test_search_adds_ilike_filter(self) -> None:
        stmt = _build_donor_list_query(
            search="jan",
            country=None,
            has_gdpr_consent=None,
            sort_by="created_at",
            sort_order="desc",
        )
        compiled = str(stmt.compile())
        assert "LIKE" in compiled.upper()

    def test_country_filter(self) -> None:
        stmt = _build_donor_list_query(
            search=None,
            country="NL",
            has_gdpr_consent=None,
            sort_by="created_at",
            sort_order="desc",
        )
        compiled = str(stmt.compile())
        assert "country" in compiled

    def test_gdpr_consent_true_filter(self) -> None:
        stmt = _build_donor_list_query(
            search=None,
            country=None,
            has_gdpr_consent=True,
            sort_by="created_at",
            sort_order="desc",
        )
        compiled = str(stmt.compile())
        assert "gdpr_consent_at" in compiled

    def test_gdpr_consent_false_filter(self) -> None:
        stmt = _build_donor_list_query(
            search=None,
            country=None,
            has_gdpr_consent=False,
            sort_by="created_at",
            sort_order="desc",
        )
        compiled = str(stmt.compile())
        assert "gdpr_consent_at" in compiled

    def test_sort_by_full_name_asc(self) -> None:
        stmt = _build_donor_list_query(
            search=None,
            country=None,
            has_gdpr_consent=None,
            sort_by="full_name",
            sort_order="asc",
        )
        compiled = str(stmt.compile())
        assert "full_name" in compiled

    def test_sort_by_email_desc(self) -> None:
        stmt = _build_donor_list_query(
            search=None,
            country=None,
            has_gdpr_consent=None,
            sort_by="email",
            sort_order="desc",
        )
        compiled = str(stmt.compile())
        assert "email" in compiled


# ---------------------------------------------------------------------------
# Allowed sort fields constant
# ---------------------------------------------------------------------------


def test_allowed_sort_fields_contains_expected_values() -> None:
    assert "full_name" in _ALLOWED_SORT_FIELDS
    assert "email" in _ALLOWED_SORT_FIELDS
    assert "created_at" in _ALLOWED_SORT_FIELDS
    assert len(_ALLOWED_SORT_FIELDS) == 3


# ---------------------------------------------------------------------------
# DonorListResponse schema
# ---------------------------------------------------------------------------


class TestDonorListResponse:
    """Tests for the DonorListResponse Pydantic schema."""

    def test_inherits_from_donor_response(self) -> None:
        assert issubclass(DonorListResponse, DonorResponse)

    def test_default_donation_stats(self) -> None:
        """DonorListResponse has default zero values for donation stats."""
        schema = DonorListResponse.model_json_schema()
        props = schema["properties"]
        assert "total_donations" in props
        assert "total_donated_cents" in props

    def test_from_dict_with_stats(self) -> None:
        """DonorListResponse can be constructed with donation stats."""
        data = {
            "id": "00000000-0000-0000-0000-000000000099",
            "full_name": "Test Donor",
            "email": "test@example.com",
            "country": "NL",
            "currency_preference": "EUR",
            "gdpr_consent_at": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "total_donations": 5,
            "total_donated_cents": 50000,
        }
        obj = DonorListResponse(**data)
        assert obj.total_donations == 5
        assert obj.total_donated_cents == 50000

    def test_from_dict_without_stats_uses_defaults(self) -> None:
        """DonorListResponse defaults to zero stats when not provided."""
        data = {
            "id": "00000000-0000-0000-0000-000000000099",
            "full_name": "Test Donor",
            "email": "test@example.com",
            "country": None,
            "currency_preference": "EUR",
            "gdpr_consent_at": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        obj = DonorListResponse(**data)
        assert obj.total_donations == 0
        assert obj.total_donated_cents == 0
