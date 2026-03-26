"""Unit tests for GDPR data export service logic.

Tests data aggregation, export request lifecycle, and subject-type routing
with mocked database sessions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.data_export import DataExportStatus, DataSubjectType
from src.services.gdpr_export_service import (
    create_export_request,
    get_export_request,
    list_export_requests,
    mark_downloaded,
)


class TestCreateExportRequest:
    """Tests for create_export_request function."""

    @pytest.mark.asyncio
    async def test_creates_request_and_completes_for_donor(self) -> None:
        db = AsyncMock()
        donor_id = uuid4()

        donor_mock = MagicMock()
        donor_mock.id = donor_id
        donor_mock.full_name = "Jan de Vries"
        donor_mock.email = "jan@example.nl"
        donor_mock.country = "NL"
        donor_mock.currency_preference = "EUR"
        donor_mock.gdpr_consent_at = datetime(2025, 1, 15, tzinfo=UTC)
        donor_mock.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        donor_mock.updated_at = datetime(2025, 6, 1, tzinfo=UTC)

        db.get.return_value = donor_mock

        # Mock the execute calls for donations, in-kind, contacts
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute.return_value = empty_result

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.DONOR,
            subject_id=donor_id,
            subject_email="jan@example.nl",
            requested_by_user_id=uuid4(),
        )

        assert result is not None
        assert result.status == DataExportStatus.COMPLETED.value
        assert result.export_data is not None
        assert result.export_data["subject_type"] == "donor"
        assert result.export_data["profile"]["full_name"] == "Jan de Vries"
        assert result.completed_at is not None
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_request_and_completes_for_adopter(self) -> None:
        db = AsyncMock()
        adopter_id = uuid4()

        adopter_mock = MagicMock()
        adopter_mock.id = adopter_id
        adopter_mock.full_name = "Maria Lopez"
        adopter_mock.email = "maria@example.py"
        adopter_mock.phone = "+595981234567"
        adopter_mock.address = "Asuncion, Paraguay"
        adopter_mock.gdpr_consent_at = None
        adopter_mock.created_at = datetime(2025, 3, 1, tzinfo=UTC)
        adopter_mock.updated_at = datetime(2025, 3, 1, tzinfo=UTC)

        db.get.return_value = adopter_mock

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute.return_value = empty_result

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.ADOPTER,
            subject_id=adopter_id,
            subject_email="maria@example.py",
        )

        assert result.status == DataExportStatus.COMPLETED.value
        assert result.export_data["subject_type"] == "adopter"
        assert result.export_data["profile"]["phone"] == "+595981234567"

    @pytest.mark.asyncio
    async def test_creates_request_and_completes_for_staff(self) -> None:
        db = AsyncMock()
        user_id = uuid4()

        user_mock = MagicMock()
        user_mock.id = user_id
        user_mock.email = "admin@refugio.py"
        user_mock.role = "admin"
        user_mock.is_active = True
        user_mock.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        user_mock.updated_at = datetime(2025, 6, 1, tzinfo=UTC)

        db.get.return_value = user_mock

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute.return_value = empty_result

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.STAFF,
            subject_id=user_id,
            subject_email="admin@refugio.py",
        )

        assert result.status == DataExportStatus.COMPLETED.value
        assert result.export_data["subject_type"] == "staff"
        assert result.export_data["profile"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_sets_expires_at(self) -> None:
        db = AsyncMock()
        donor_id = uuid4()

        donor_mock = MagicMock()
        donor_mock.id = donor_id
        donor_mock.full_name = "Test"
        donor_mock.email = "test@example.com"
        donor_mock.country = None
        donor_mock.currency_preference = "EUR"
        donor_mock.gdpr_consent_at = None
        donor_mock.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        donor_mock.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        db.get.return_value = donor_mock
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute.return_value = empty_result

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.DONOR,
            subject_id=donor_id,
            subject_email="test@example.com",
        )

        assert result.expires_at is not None

    @pytest.mark.asyncio
    async def test_handles_aggregation_failure(self) -> None:
        db = AsyncMock()
        donor_id = uuid4()

        # db.get raises to simulate failure during aggregation
        db.get.side_effect = RuntimeError("DB connection lost")

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.DONOR,
            subject_id=donor_id,
            subject_email="test@example.com",
        )

        assert result.status == DataExportStatus.FAILED.value
        assert result.error_message == "Export generation failed"


class TestDonorDataAggregation:
    """Tests for donor data aggregation with related records."""

    @pytest.mark.asyncio
    async def test_includes_donation_history(self) -> None:
        db = AsyncMock()
        donor_id = uuid4()

        donor_mock = MagicMock()
        donor_mock.id = donor_id
        donor_mock.full_name = "Donor With History"
        donor_mock.email = "donor@example.com"
        donor_mock.country = "DE"
        donor_mock.currency_preference = "EUR"
        donor_mock.gdpr_consent_at = datetime(2025, 2, 1, tzinfo=UTC)
        donor_mock.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        donor_mock.updated_at = datetime(2025, 6, 1, tzinfo=UTC)

        donation_mock = MagicMock()
        donation_mock.id = uuid4()
        donation_mock.amount_cents = 5000
        donation_mock.currency = "EUR"
        donation_mock.payment_method = "card"
        donation_mock.status = "completed"
        donation_mock.receipt_number = "RCP-001"
        donation_mock.notes = None
        donation_mock.created_at = datetime(2025, 3, 15, tzinfo=UTC)

        db.get.return_value = donor_mock

        # First execute call = donations, second = in-kind, third = contacts
        donations_result = MagicMock()
        donations_result.scalars.return_value.all.return_value = [donation_mock]

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []

        db.execute.side_effect = [donations_result, empty_result, empty_result]

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.DONOR,
            subject_id=donor_id,
            subject_email="donor@example.com",
        )

        assert len(result.export_data["donations"]) == 1
        assert result.export_data["donations"][0]["amount_cents"] == 5000
        assert result.export_data["donations"][0]["currency"] == "EUR"

    @pytest.mark.asyncio
    async def test_returns_error_for_nonexistent_donor(self) -> None:
        db = AsyncMock()
        donor_id = uuid4()
        db.get.return_value = None

        # Still need execute mocks for the empty queries
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute.return_value = empty_result

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.DONOR,
            subject_id=donor_id,
            subject_email="missing@example.com",
        )

        assert result.status == DataExportStatus.COMPLETED.value
        assert "error" in result.export_data


class TestAdopterDataAggregation:
    """Tests for adopter data aggregation."""

    @pytest.mark.asyncio
    async def test_includes_adoption_requests(self) -> None:
        db = AsyncMock()
        adopter_id = uuid4()

        adopter_mock = MagicMock()
        adopter_mock.id = adopter_id
        adopter_mock.full_name = "Test Adopter"
        adopter_mock.email = "adopter@example.com"
        adopter_mock.phone = None
        adopter_mock.address = None
        adopter_mock.gdpr_consent_at = None
        adopter_mock.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        adopter_mock.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        ar_mock = MagicMock()
        ar_mock.id = uuid4()
        ar_mock.animal_id = uuid4()
        ar_mock.status = "approved"
        ar_mock.submitted_at = datetime(2025, 2, 1, tzinfo=UTC)
        ar_mock.decided_at = datetime(2025, 2, 5, tzinfo=UTC)
        ar_mock.notes = "Good match"
        ar_mock.created_at = datetime(2025, 2, 1, tzinfo=UTC)

        db.get.return_value = adopter_mock

        requests_result = MagicMock()
        requests_result.scalars.return_value.all.return_value = [ar_mock]

        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []

        db.execute.side_effect = [requests_result, empty_result]

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.ADOPTER,
            subject_id=adopter_id,
            subject_email="adopter@example.com",
        )

        assert len(result.export_data["adoption_requests"]) == 1
        assert result.export_data["adoption_requests"][0]["status"] == "approved"


class TestStaffDataAggregation:
    """Tests for staff data aggregation."""

    @pytest.mark.asyncio
    async def test_includes_audit_trail(self) -> None:
        db = AsyncMock()
        user_id = uuid4()

        user_mock = MagicMock()
        user_mock.id = user_id
        user_mock.email = "staff@refugio.py"
        user_mock.role = "staff"
        user_mock.is_active = True
        user_mock.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        user_mock.updated_at = datetime(2025, 1, 1, tzinfo=UTC)

        audit_mock = MagicMock()
        audit_mock.id = uuid4()
        audit_mock.action = "create"
        audit_mock.resource_type = "animal"
        audit_mock.resource_id = str(uuid4())
        audit_mock.timestamp = datetime(2025, 3, 1, tzinfo=UTC)
        audit_mock.ip_address = "192.168.1.1"

        db.get.return_value = user_mock

        # First execute = consents, second = audit logs
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []

        audit_result = MagicMock()
        audit_result.scalars.return_value.all.return_value = [audit_mock]

        db.execute.side_effect = [empty_result, audit_result]

        result = await create_export_request(
            db=db,
            subject_type=DataSubjectType.STAFF,
            subject_id=user_id,
            subject_email="staff@refugio.py",
        )

        assert len(result.export_data["audit_trail"]) == 1
        assert result.export_data["audit_trail"][0]["action"] == "create"


class TestGetExportRequest:
    """Tests for get_export_request function."""

    @pytest.mark.asyncio
    async def test_returns_request(self) -> None:
        export_req = MagicMock()
        db = AsyncMock()
        db.get.return_value = export_req

        result = await get_export_request(db, uuid4())
        assert result is export_req

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        result = await get_export_request(db, uuid4())
        assert result is None


class TestListExportRequests:
    """Tests for list_export_requests function."""

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        r1 = MagicMock()
        r2 = MagicMock()

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [r1, r2]
        db.execute.return_value = mock_result

        result = await list_export_requests(db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await list_export_requests(db)
        assert result == []


class TestMarkDownloaded:
    """Tests for mark_downloaded function."""

    @pytest.mark.asyncio
    async def test_sets_downloaded_at(self) -> None:
        export_req = MagicMock()
        export_req.downloaded_at = None
        db = AsyncMock()

        result = await mark_downloaded(db, export_req)

        assert result.downloaded_at is not None
        db.flush.assert_awaited_once()
