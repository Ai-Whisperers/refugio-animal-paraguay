"""Unit tests for impact email service."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.impact_email_log import VALID_EMAIL_STATUSES, EmailStatus, ImpactEmailLog
from src.services.impact_email_service import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_RETRY_COUNT,
    DuplicateEmailError,
    EmailLogNotFoundError,
    ImpactEmailError,
    InvalidEmailError,
    create_email_log,
    get_campaign_stats,
    get_email_log,
    increment_retry,
    list_email_logs,
    update_email_status,
)

# --- Error class tests ---


class TestErrorClasses:
    """Test error class hierarchy."""

    def test_impact_email_error_is_exception(self) -> None:
        assert issubclass(ImpactEmailError, Exception)

    def test_email_log_not_found_error_is_impact_email_error(self) -> None:
        assert issubclass(EmailLogNotFoundError, ImpactEmailError)

    def test_duplicate_email_error_is_impact_email_error(self) -> None:
        assert issubclass(DuplicateEmailError, ImpactEmailError)

    def test_invalid_email_error_is_impact_email_error(self) -> None:
        assert issubclass(InvalidEmailError, ImpactEmailError)


# --- Constants tests ---


class TestConstants:
    """Test module constants."""

    def test_default_page_size(self) -> None:
        assert DEFAULT_PAGE_SIZE == 20

    def test_max_page_size(self) -> None:
        assert MAX_PAGE_SIZE == 100

    def test_max_retry_count(self) -> None:
        assert MAX_RETRY_COUNT == 3


# --- create_email_log tests ---


class TestCreateEmailLog:
    """Test create_email_log function."""

    @pytest.fixture()
    def mock_db(self) -> AsyncMock:
        db = AsyncMock()
        return db

    @pytest.fixture()
    def valid_params(self) -> dict:
        return {
            "donor_id": uuid4(),
            "email_address": "donor@example.com",
            "subject": "Your Impact Report - March 2026",
            "report_month": 3,
            "report_year": 2026,
            "donation_total": 150000.00,
            "currency": "PYG",
            "animals_rescued": 5,
            "animals_adopted": 3,
            "castrations_funded": 10,
            "medical_treatments": 8,
        }

    @pytest.mark.asyncio()
    async def test_raises_on_empty_email(self, mock_db: AsyncMock, valid_params: dict) -> None:
        valid_params["email_address"] = ""
        with pytest.raises(InvalidEmailError, match="Email address is required"):
            await create_email_log(db=mock_db, **valid_params)

    @pytest.mark.asyncio()
    async def test_raises_on_whitespace_email(self, mock_db: AsyncMock, valid_params: dict) -> None:
        valid_params["email_address"] = "   "
        with pytest.raises(InvalidEmailError, match="Email address is required"):
            await create_email_log(db=mock_db, **valid_params)

    @pytest.mark.asyncio()
    async def test_raises_on_invalid_month_zero(
        self, mock_db: AsyncMock, valid_params: dict
    ) -> None:
        valid_params["report_month"] = 0
        with pytest.raises(InvalidEmailError, match="Invalid month 0"):
            await create_email_log(db=mock_db, **valid_params)

    @pytest.mark.asyncio()
    async def test_raises_on_invalid_month_thirteen(
        self, mock_db: AsyncMock, valid_params: dict
    ) -> None:
        valid_params["report_month"] = 13
        with pytest.raises(InvalidEmailError, match="Invalid month 13"):
            await create_email_log(db=mock_db, **valid_params)

    @pytest.mark.asyncio()
    async def test_raises_on_invalid_year(self, mock_db: AsyncMock, valid_params: dict) -> None:
        valid_params["report_year"] = 2019
        with pytest.raises(InvalidEmailError, match="Invalid year 2019"):
            await create_email_log(db=mock_db, **valid_params)

    @pytest.mark.asyncio()
    async def test_raises_on_negative_donation(
        self, mock_db: AsyncMock, valid_params: dict
    ) -> None:
        valid_params["donation_total"] = -100.0
        with pytest.raises(InvalidEmailError, match="Donation total cannot be negative"):
            await create_email_log(db=mock_db, **valid_params)

    @pytest.mark.asyncio()
    async def test_raises_on_duplicate(self, mock_db: AsyncMock, valid_params: dict) -> None:
        scalar_mock = MagicMock()
        scalar_mock.scalar_one.return_value = 1
        mock_db.execute.return_value = scalar_mock

        with pytest.raises(DuplicateEmailError, match="already exists"):
            await create_email_log(db=mock_db, **valid_params)

    @pytest.mark.asyncio()
    async def test_creates_log_successfully(self, mock_db: AsyncMock, valid_params: dict) -> None:
        # Duplicate check returns 0
        scalar_mock = MagicMock()
        scalar_mock.scalar_one.return_value = 0
        mock_db.execute.return_value = scalar_mock

        created_log = MagicMock(spec=ImpactEmailLog)
        created_log.id = uuid4()
        created_log.donor_id = valid_params["donor_id"]
        created_log.email_address = valid_params["email_address"]
        created_log.subject = valid_params["subject"]
        created_log.report_month = valid_params["report_month"]
        created_log.report_year = valid_params["report_year"]
        created_log.donation_total = valid_params["donation_total"]
        created_log.currency = valid_params["currency"]
        created_log.animals_rescued = valid_params["animals_rescued"]
        created_log.animals_adopted = valid_params["animals_adopted"]
        created_log.castrations_funded = valid_params["castrations_funded"]
        created_log.medical_treatments = valid_params["medical_treatments"]
        created_log.status = EmailStatus.PENDING.value
        created_log.sent_at = None
        created_log.opened_at = None
        created_log.failure_reason = None
        created_log.retry_count = 0
        created_log.created_at = datetime.now(UTC)

        async def fake_refresh(obj: object) -> None:
            pass

        mock_db.flush = AsyncMock(return_value=None)
        mock_db.refresh = fake_refresh

        # Capture the added object and set its attributes
        def capture_add(obj: object) -> None:
            for attr in (
                "id",
                "donor_id",
                "email_address",
                "subject",
                "report_month",
                "report_year",
                "donation_total",
                "currency",
                "animals_rescued",
                "animals_adopted",
                "castrations_funded",
                "medical_treatments",
                "status",
                "sent_at",
                "opened_at",
                "failure_reason",
                "retry_count",
                "created_at",
            ):
                setattr(obj, attr, getattr(created_log, attr))

        mock_db.add.side_effect = capture_add

        result = await create_email_log(db=mock_db, **valid_params)

        assert result["donor_id"] == valid_params["donor_id"]
        assert result["status"] == EmailStatus.PENDING.value
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_strips_email_whitespace(self, mock_db: AsyncMock, valid_params: dict) -> None:
        valid_params["email_address"] = "  donor@example.com  "

        scalar_mock = MagicMock()
        scalar_mock.scalar_one.return_value = 0
        mock_db.execute.return_value = scalar_mock

        async def fake_refresh(obj: object) -> None:
            pass

        mock_db.flush = AsyncMock(return_value=None)
        mock_db.refresh = fake_refresh

        # db.add is synchronous in SQLAlchemy — use MagicMock
        captured: list = []

        def capture_add(obj: object) -> None:
            captured.append(obj)

        mock_db.add = MagicMock(side_effect=capture_add)

        await create_email_log(db=mock_db, **valid_params)

        # The service strips email before storing
        assert captured[0].email_address == "donor@example.com"


# --- get_email_log tests ---


class TestGetEmailLog:
    """Test get_email_log function."""

    @pytest.mark.asyncio()
    async def test_raises_when_not_found(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(EmailLogNotFoundError):
            await get_email_log(db=db, log_id=uuid4())

    @pytest.mark.asyncio()
    async def test_returns_log_dict(self) -> None:
        db = AsyncMock()
        log_obj = MagicMock(spec=ImpactEmailLog)
        log_obj.id = uuid4()
        log_obj.donor_id = uuid4()
        log_obj.email_address = "test@example.com"
        log_obj.subject = "Test"
        log_obj.report_month = 1
        log_obj.report_year = 2026
        log_obj.donation_total = 100.0
        log_obj.currency = "PYG"
        log_obj.animals_rescued = 0
        log_obj.animals_adopted = 0
        log_obj.castrations_funded = 0
        log_obj.medical_treatments = 0
        log_obj.status = "pending"
        log_obj.sent_at = None
        log_obj.opened_at = None
        log_obj.failure_reason = None
        log_obj.retry_count = 0
        log_obj.created_at = datetime.now(UTC)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log_obj
        db.execute.return_value = result_mock

        result = await get_email_log(db=db, log_id=log_obj.id)
        assert result["id"] == log_obj.id
        assert result["email_address"] == "test@example.com"


# --- list_email_logs tests ---


class TestListEmailLogs:
    """Test list_email_logs function."""

    @pytest.mark.asyncio()
    async def test_returns_paginated_results(self) -> None:
        db = AsyncMock()

        # Count query
        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 0

        # List query
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        list_mock = MagicMock()
        list_mock.scalars.return_value = scalars_mock

        db.execute.side_effect = [count_mock, list_mock]

        result = await list_email_logs(db=db)
        assert result["total"] == 0
        assert result["email_logs"] == []
        assert result["limit"] == DEFAULT_PAGE_SIZE
        assert result["offset"] == 0

    @pytest.mark.asyncio()
    async def test_applies_filters(self) -> None:
        db = AsyncMock()
        donor_id = uuid4()

        count_mock = MagicMock()
        count_mock.scalar_one.return_value = 0

        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        list_mock = MagicMock()
        list_mock.scalars.return_value = scalars_mock

        db.execute.side_effect = [count_mock, list_mock]

        result = await list_email_logs(
            db=db,
            donor_id=donor_id,
            status_filter="sent",
            report_year=2026,
            report_month=3,
            limit=10,
            offset=5,
        )
        assert result["total"] == 0
        assert result["limit"] == 10
        assert result["offset"] == 5


# --- update_email_status tests ---


class TestUpdateEmailStatus:
    """Test update_email_status function."""

    def _make_log(self, **overrides: object) -> MagicMock:
        log = MagicMock(spec=ImpactEmailLog)
        log.id = overrides.get("id", uuid4())
        log.donor_id = overrides.get("donor_id", uuid4())
        log.email_address = overrides.get("email_address", "test@example.com")
        log.subject = overrides.get("subject", "Test")
        log.report_month = overrides.get("report_month", 1)
        log.report_year = overrides.get("report_year", 2026)
        log.donation_total = overrides.get("donation_total", 100.0)
        log.currency = overrides.get("currency", "PYG")
        log.animals_rescued = overrides.get("animals_rescued", 0)
        log.animals_adopted = overrides.get("animals_adopted", 0)
        log.castrations_funded = overrides.get("castrations_funded", 0)
        log.medical_treatments = overrides.get("medical_treatments", 0)
        log.status = overrides.get("status", "pending")
        log.sent_at = overrides.get("sent_at")
        log.opened_at = overrides.get("opened_at")
        log.failure_reason = overrides.get("failure_reason")
        log.retry_count = overrides.get("retry_count", 0)
        log.created_at = overrides.get("created_at", datetime.now(UTC))
        return log

    @pytest.mark.asyncio()
    async def test_raises_when_not_found(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(EmailLogNotFoundError):
            await update_email_status(db=db, log_id=uuid4(), new_status="sent")

    @pytest.mark.asyncio()
    async def test_raises_on_invalid_status(self) -> None:
        db = AsyncMock()
        log = self._make_log()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log
        db.execute.return_value = result_mock

        with pytest.raises(InvalidEmailError, match="Invalid status"):
            await update_email_status(db=db, log_id=log.id, new_status="invalid_status")

    @pytest.mark.asyncio()
    async def test_sets_sent_at_on_sent_status(self) -> None:
        db = AsyncMock()
        log = self._make_log()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log
        db.execute.return_value = result_mock

        await update_email_status(db=db, log_id=log.id, new_status=EmailStatus.SENT.value)
        assert log.status == EmailStatus.SENT.value
        assert log.sent_at is not None

    @pytest.mark.asyncio()
    async def test_sets_opened_at_on_opened_status(self) -> None:
        db = AsyncMock()
        log = self._make_log()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log
        db.execute.return_value = result_mock

        await update_email_status(db=db, log_id=log.id, new_status=EmailStatus.OPENED.value)
        assert log.status == EmailStatus.OPENED.value
        assert log.opened_at is not None

    @pytest.mark.asyncio()
    async def test_sets_failure_reason_on_failed(self) -> None:
        db = AsyncMock()
        log = self._make_log()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log
        db.execute.return_value = result_mock

        await update_email_status(
            db=db, log_id=log.id, new_status=EmailStatus.FAILED.value, failure_reason="SMTP timeout"
        )
        assert log.failure_reason == "SMTP timeout"

    @pytest.mark.asyncio()
    async def test_sets_failure_reason_on_bounced(self) -> None:
        db = AsyncMock()
        log = self._make_log()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log
        db.execute.return_value = result_mock

        await update_email_status(
            db=db,
            log_id=log.id,
            new_status=EmailStatus.BOUNCED.value,
            failure_reason="Mailbox full",
        )
        assert log.failure_reason == "Mailbox full"


# --- increment_retry tests ---


class TestIncrementRetry:
    """Test increment_retry function."""

    @pytest.mark.asyncio()
    async def test_raises_when_not_found(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(EmailLogNotFoundError):
            await increment_retry(db=db, log_id=uuid4())

    @pytest.mark.asyncio()
    async def test_raises_when_max_retries_reached(self) -> None:
        db = AsyncMock()
        log = MagicMock(spec=ImpactEmailLog)
        log.id = uuid4()
        log.retry_count = MAX_RETRY_COUNT

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log
        db.execute.return_value = result_mock

        with pytest.raises(InvalidEmailError, match="Max retry count"):
            await increment_retry(db=db, log_id=log.id)

    @pytest.mark.asyncio()
    async def test_increments_and_resets_status(self) -> None:
        db = AsyncMock()
        log = MagicMock(spec=ImpactEmailLog)
        log.id = uuid4()
        log.donor_id = uuid4()
        log.email_address = "test@example.com"
        log.subject = "Test"
        log.report_month = 1
        log.report_year = 2026
        log.donation_total = 100.0
        log.currency = "PYG"
        log.animals_rescued = 0
        log.animals_adopted = 0
        log.castrations_funded = 0
        log.medical_treatments = 0
        log.status = EmailStatus.FAILED.value
        log.sent_at = None
        log.opened_at = None
        log.failure_reason = "Previous failure"
        log.retry_count = 1
        log.created_at = datetime.now(UTC)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = log
        db.execute.return_value = result_mock

        await increment_retry(db=db, log_id=log.id)
        assert log.retry_count == 2
        assert log.status == EmailStatus.PENDING.value
        assert log.failure_reason is None


# --- get_campaign_stats tests ---


class TestGetCampaignStats:
    """Test get_campaign_stats function."""

    @pytest.mark.asyncio()
    async def test_returns_stats_structure(self) -> None:
        db = AsyncMock()

        # Total count + one count per status
        total_mock = MagicMock()
        total_mock.scalar_one.return_value = 10

        status_mocks = []
        for _status in VALID_EMAIL_STATUSES:
            m = MagicMock()
            m.scalar_one.return_value = 0
            status_mocks.append(m)

        db.execute.side_effect = [total_mock, *status_mocks]

        result = await get_campaign_stats(db=db, report_year=2026, report_month=3)
        assert result["report_year"] == 2026
        assert result["report_month"] == 3
        assert result["total"] == 10
        assert "by_status" in result
        assert len(result["by_status"]) == len(VALID_EMAIL_STATUSES)
