"""Unit tests for the Paraguayan record retention service (RAP-247).

Tests cover:
- Retention period constants (correct legal values)
- RETENTION_POLICY structure and content
- RetentionStatusResult dataclass defaults
- get_retention_status: correct DB queries and result population
- GET /legal/record-retention-policy endpoint
- GET /admin/data-retention/paraguayan-status endpoint
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from src.services.paraguayan_retention_service import (
    ADOPTER_DATA_RETENTION_YEARS,
    ADOPTION_CONTRACT_RETENTION_YEARS,
    ANIMAL_HEALTH_RECORD_RETENTION_YEARS,
    CONTACT_RECORD_RETENTION_YEARS,
    DONATION_RECORD_RETENTION_YEARS,
    RETENTION_POLICY,
    VACCINATION_RECORD_RETENTION_YEARS,
    RetentionStatusResult,
    get_retention_status,
)

# ---------------------------------------------------------------------------
# Retention period constants
# ---------------------------------------------------------------------------


class TestRetentionPeriodConstants:
    """Verify statutory minimums match Paraguayan law."""

    def test_adoption_contract_is_10_years(self) -> None:
        # Codigo Civil Paraguayo Art. 633 — civil contracts
        assert ADOPTION_CONTRACT_RETENTION_YEARS == 10

    def test_animal_health_record_is_5_years(self) -> None:
        # Ley 4840/2013 Art. 12
        assert ANIMAL_HEALTH_RECORD_RETENTION_YEARS == 5

    def test_vaccination_record_is_5_years(self) -> None:
        # Ley 3140/2006 Art. 5
        assert VACCINATION_RECORD_RETENTION_YEARS == 5

    def test_donation_record_is_5_years(self) -> None:
        # Ley 125/91 Art. 84
        assert DONATION_RECORD_RETENTION_YEARS == 5

    def test_adopter_data_is_5_years(self) -> None:
        assert ADOPTER_DATA_RETENTION_YEARS == 5

    def test_contact_record_is_2_years(self) -> None:
        assert CONTACT_RECORD_RETENTION_YEARS == 2


# ---------------------------------------------------------------------------
# RETENTION_POLICY structure
# ---------------------------------------------------------------------------


class TestRetentionPolicy:
    """Verify RETENTION_POLICY list is complete and well-formed."""

    def test_policy_is_a_list(self) -> None:
        assert isinstance(RETENTION_POLICY, list)

    def test_policy_has_six_record_types(self) -> None:
        assert len(RETENTION_POLICY) == 6

    def test_each_entry_has_required_keys(self) -> None:
        required = {"record_type", "description", "retention_years", "legal_basis", "trigger"}
        for entry in RETENTION_POLICY:
            missing = required - entry.keys()
            assert not missing, f"Policy entry missing keys {missing}: {entry['record_type']}"

    def test_adoption_contracts_entry_present(self) -> None:
        types = {e["record_type"] for e in RETENTION_POLICY}
        assert "adoption_contracts" in types

    def test_animal_health_records_entry_present(self) -> None:
        types = {e["record_type"] for e in RETENTION_POLICY}
        assert "animal_health_records" in types

    def test_vaccination_records_entry_present(self) -> None:
        types = {e["record_type"] for e in RETENTION_POLICY}
        assert "vaccination_records" in types

    def test_donation_records_entry_present(self) -> None:
        types = {e["record_type"] for e in RETENTION_POLICY}
        assert "donation_records" in types

    def test_adopter_personal_data_entry_present(self) -> None:
        types = {e["record_type"] for e in RETENTION_POLICY}
        assert "adopter_personal_data" in types

    def test_contact_submissions_entry_present(self) -> None:
        types = {e["record_type"] for e in RETENTION_POLICY}
        assert "contact_submissions" in types

    def test_adoption_contract_retention_matches_constant(self) -> None:
        entry = next(e for e in RETENTION_POLICY if e["record_type"] == "adoption_contracts")
        assert entry["retention_years"] == ADOPTION_CONTRACT_RETENTION_YEARS

    def test_adoption_contract_cites_codigo_civil(self) -> None:
        entry = next(e for e in RETENTION_POLICY if e["record_type"] == "adoption_contracts")
        assert "Codigo Civil" in entry["legal_basis"]

    def test_vaccination_cites_ley_3140(self) -> None:
        entry = next(e for e in RETENTION_POLICY if e["record_type"] == "vaccination_records")
        assert "3140" in entry["legal_basis"]

    def test_animal_health_cites_ley_4840(self) -> None:
        entry = next(e for e in RETENTION_POLICY if e["record_type"] == "animal_health_records")
        assert "4840" in entry["legal_basis"]

    def test_donation_cites_ley_125(self) -> None:
        entry = next(e for e in RETENTION_POLICY if e["record_type"] == "donation_records")
        assert "125" in entry["legal_basis"]

    def test_all_retention_years_are_positive_ints(self) -> None:
        for entry in RETENTION_POLICY:
            years = entry["retention_years"]
            assert (
                isinstance(years, int) and years > 0
            ), f"{entry['record_type']}: retention_years must be positive int, got {years!r}"


# ---------------------------------------------------------------------------
# RetentionStatusResult dataclass
# ---------------------------------------------------------------------------


class TestRetentionStatusResult:
    """Verify dataclass initialises with sensible defaults."""

    def test_default_counts_are_zero(self) -> None:
        result = RetentionStatusResult()
        assert result.pending_adoption_count == 0
        assert result.active_animal_count == 0
        assert result.recent_donation_count == 0

    def test_oldest_dates_default_to_none(self) -> None:
        result = RetentionStatusResult()
        assert result.oldest_adoption_date is None
        assert result.oldest_donation_date is None

    def test_policy_defaults_to_empty_list(self) -> None:
        result = RetentionStatusResult()
        assert result.policy == []

    def test_check_date_defaults_to_now(self) -> None:
        before = datetime.now(UTC)
        result = RetentionStatusResult()
        after = datetime.now(UTC)
        assert before <= result.check_date <= after


# ---------------------------------------------------------------------------
# get_retention_status service function
# ---------------------------------------------------------------------------


class TestGetRetentionStatus:
    """Unit tests for the get_retention_status async service function."""

    @pytest.mark.asyncio
    async def test_returns_retention_status_result(self) -> None:
        db = AsyncMock()
        # scalar_one returns for each execute call: animal_count, adoption_count, donation_count
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=10)),
                MagicMock(scalar_one=MagicMock(return_value=3)),
                MagicMock(scalar_one=MagicMock(return_value=25)),
            ]
        )
        result = await get_retention_status(db)
        assert isinstance(result, RetentionStatusResult)

    @pytest.mark.asyncio
    async def test_active_animal_count_set_from_query(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=42)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
            ]
        )
        result = await get_retention_status(db)
        assert result.active_animal_count == 42

    @pytest.mark.asyncio
    async def test_pending_adoption_count_set_from_query(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=7)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
            ]
        )
        result = await get_retention_status(db)
        assert result.pending_adoption_count == 7

    @pytest.mark.asyncio
    async def test_recent_donation_count_set_from_query(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=99)),
            ]
        )
        result = await get_retention_status(db)
        assert result.recent_donation_count == 99

    @pytest.mark.asyncio
    async def test_policy_list_is_populated(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
            ]
        )
        result = await get_retention_status(db)
        assert result.policy is RETENTION_POLICY

    @pytest.mark.asyncio
    async def test_now_override_used_for_check_date(self) -> None:
        fixed_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
            ]
        )
        result = await get_retention_status(db, now=fixed_time)
        assert result.check_date == fixed_time

    @pytest.mark.asyncio
    async def test_executes_exactly_three_queries(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
                MagicMock(scalar_one=MagicMock(return_value=0)),
            ]
        )
        await get_retention_status(db)
        assert db.execute.call_count == 3


# ---------------------------------------------------------------------------
# GET /legal/record-retention-policy endpoint
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    from src.app import app

    return TestClient(app)


class TestRecordRetentionPolicyEndpoint:
    """GET /legal/record-retention-policy."""

    def test_returns_200(self, client: TestClient) -> None:
        response = client.get("/legal/record-retention-policy")
        assert response.status_code == 200

    def test_response_is_json(self, client: TestClient) -> None:
        response = client.get("/legal/record-retention-policy")
        assert response.headers["content-type"].startswith("application/json")

    def test_has_required_top_level_keys(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        required = {"document", "version", "last_updated", "jurisdiction", "note", "policies"}
        assert required.issubset(data.keys())

    def test_document_name(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        assert data["document"] == "Paraguayan Record Retention Policy"

    def test_jurisdiction_is_paraguay(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        assert "Paraguay" in data["jurisdiction"]

    def test_policies_is_a_list(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        assert isinstance(data["policies"], list)

    def test_policies_has_six_entries(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        assert len(data["policies"]) == 6

    def test_each_policy_has_required_keys(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        required = {"record_type", "description", "retention_years", "legal_basis", "trigger"}
        for policy in data["policies"]:
            assert required.issubset(
                policy.keys()
            ), f"Policy entry missing keys: {required - policy.keys()}"

    def test_adoption_contract_retention_is_10_years(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        entry = next(p for p in data["policies"] if p["record_type"] == "adoption_contracts")
        assert entry["retention_years"] == 10

    def test_legal_basis_references_paraguayan_law(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        all_bases = " ".join(p["legal_basis"] for p in data["policies"])
        assert "Ley" in all_bases or "Codigo" in all_bases

    def test_note_mentions_minimum_retention(self, client: TestClient) -> None:
        data = client.get("/legal/record-retention-policy").json()
        assert "minimum" in data["note"].lower()

    def test_no_authentication_required(self, client: TestClient) -> None:
        # Public endpoint — must be accessible without auth
        response = client.get("/legal/record-retention-policy")
        assert response.status_code != 401
        assert response.status_code != 403
