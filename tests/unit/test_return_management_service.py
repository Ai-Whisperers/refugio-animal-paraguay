"""Unit tests for the return management service.

Tests return request creation, processing, listing, and analytics.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.return_management_service import (
    NON_AVAILABLE_CONDITIONS,
    VALID_CONDITIONS,
    AdoptionNotFoundError,
    DuplicateReturnError,
    InvalidReturnError,
    ReturnManagementError,
    ReturnNotFoundError,
    create_return_request,
    get_return_analytics,
    get_return_request,
    list_return_requests,
    process_return,
)

# -- Error classes --


class TestErrorClasses:
    """Verify error hierarchy."""

    def test_base_error(self) -> None:
        err = ReturnManagementError("base")
        assert isinstance(err, Exception)

    def test_adoption_not_found(self) -> None:
        assert isinstance(AdoptionNotFoundError("x"), ReturnManagementError)

    def test_return_not_found(self) -> None:
        assert isinstance(ReturnNotFoundError("x"), ReturnManagementError)

    def test_invalid_return(self) -> None:
        assert isinstance(InvalidReturnError("x"), ReturnManagementError)

    def test_duplicate_return(self) -> None:
        assert isinstance(DuplicateReturnError("x"), ReturnManagementError)


# -- Constants --


class TestConstants:
    """Verify module constants."""

    def test_non_available_conditions(self) -> None:
        assert "deceased" in NON_AVAILABLE_CONDITIONS
        assert "injured" in NON_AVAILABLE_CONDITIONS
        assert "healthy" not in NON_AVAILABLE_CONDITIONS

    def test_valid_conditions(self) -> None:
        assert "healthy" in VALID_CONDITIONS
        assert "injured" in VALID_CONDITIONS
        assert "sick" in VALID_CONDITIONS
        assert "deceased" in VALID_CONDITIONS


# -- create_return_request --


class TestCreateReturnRequest:
    """Tests for creating return requests."""

    @pytest.mark.asyncio
    async def test_raises_when_adoption_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(AdoptionNotFoundError):
            await create_return_request(db, uuid4(), reason="Moving away")

    @pytest.mark.asyncio
    async def test_raises_when_adoption_not_approved(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.status = "pending"

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_adoption
        db.execute.return_value = mock_result

        with pytest.raises(InvalidReturnError, match="pending"):
            await create_return_request(db, uuid4(), reason="Moving away")

    @pytest.mark.asyncio
    async def test_raises_when_duplicate_exists(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.status = "approved"

        # First call: adoption lookup, Second call: duplicate check
        mock_result_adoption = MagicMock()
        mock_result_adoption.scalar_one_or_none.return_value = mock_adoption
        mock_result_count = MagicMock()
        mock_result_count.scalar_one.return_value = 1

        db = AsyncMock()
        db.execute.side_effect = [mock_result_adoption, mock_result_count]

        with pytest.raises(DuplicateReturnError):
            await create_return_request(db, uuid4(), reason="Moving away")

    @pytest.mark.asyncio
    async def test_raises_for_invalid_condition(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.status = "approved"

        mock_result_adoption = MagicMock()
        mock_result_adoption.scalar_one_or_none.return_value = mock_adoption
        mock_result_count = MagicMock()
        mock_result_count.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.side_effect = [mock_result_adoption, mock_result_count]

        with pytest.raises(InvalidReturnError, match="Invalid animal condition"):
            await create_return_request(db, uuid4(), reason="test", animal_condition="exploded")

    @pytest.mark.asyncio
    async def test_creates_return_successfully(self) -> None:
        adoption_id = uuid4()
        mock_adoption = MagicMock()
        mock_adoption.id = adoption_id
        mock_adoption.status = "approved"

        mock_result_adoption = MagicMock()
        mock_result_adoption.scalar_one_or_none.return_value = mock_adoption
        mock_result_count = MagicMock()
        mock_result_count.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.side_effect = [mock_result_adoption, mock_result_count]

        result = await create_return_request(
            db,
            adoption_id,
            reason="Moving to new city",
            animal_condition="healthy",
            is_emergency=False,
        )

        assert result["adoption_request_id"] == adoption_id
        assert result["reason"] == "Moving to new city"
        assert result["animal_condition"] == "healthy"
        assert result["status"] == "pending"
        db.add.assert_called_once()
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_creates_emergency_return(self) -> None:
        mock_adoption = MagicMock()
        mock_adoption.status = "completed"

        mock_result_adoption = MagicMock()
        mock_result_adoption.scalar_one_or_none.return_value = mock_adoption
        mock_result_count = MagicMock()
        mock_result_count.scalar_one.return_value = 0

        db = AsyncMock()
        db.execute.side_effect = [mock_result_adoption, mock_result_count]

        result = await create_return_request(
            db,
            uuid4(),
            reason="Animal aggressive",
            animal_condition="injured",
            is_emergency=True,
        )

        assert result["is_emergency"] is True
        assert result["animal_condition"] == "injured"


# -- process_return --


class TestProcessReturn:
    """Tests for processing returns."""

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ReturnNotFoundError):
            await process_return(db, uuid4())

    @pytest.mark.asyncio
    async def test_raises_when_already_completed(self) -> None:
        return_req = MagicMock()
        return_req.status = "completed"

        db = AsyncMock()
        db.get.return_value = return_req

        with pytest.raises(InvalidReturnError, match="already completed"):
            await process_return(db, uuid4())

    @pytest.mark.asyncio
    async def test_processes_healthy_return(self) -> None:
        return_id = uuid4()
        adoption_id = uuid4()
        animal_id = uuid4()

        return_req = MagicMock()
        return_req.id = return_id
        return_req.adoption_request_id = adoption_id
        return_req.status = "pending"
        return_req.animal_condition = "healthy"

        mock_adoption = MagicMock()
        mock_adoption.id = adoption_id
        mock_adoption.animal_id = animal_id
        mock_adoption.status = "approved"

        mock_animal = MagicMock()
        mock_animal.id = animal_id
        mock_animal.status = "adopted"

        db = AsyncMock()
        db.get.return_value = return_req
        # First execute: adoption, Second: animal
        mock_result_adoption = MagicMock()
        mock_result_adoption.scalar_one_or_none.return_value = mock_adoption
        mock_result_animal = MagicMock()
        mock_result_animal.scalar_one_or_none.return_value = mock_animal
        db.execute.side_effect = [mock_result_adoption, mock_result_animal]

        result = await process_return(db, return_id, staff_notes="Processed OK")

        assert result["status"] == "completed"
        assert result["staff_notes"] == "Processed OK"
        assert mock_adoption.status == "returned"
        assert mock_animal.status == "available"

    @pytest.mark.asyncio
    async def test_processes_injured_return_to_medical_hold(self) -> None:
        return_req = MagicMock()
        return_req.id = uuid4()
        return_req.adoption_request_id = uuid4()
        return_req.status = "approved"
        return_req.animal_condition = "injured"

        mock_adoption = MagicMock()
        mock_adoption.animal_id = uuid4()

        mock_animal = MagicMock()

        db = AsyncMock()
        db.get.return_value = return_req
        mock_result_adoption = MagicMock()
        mock_result_adoption.scalar_one_or_none.return_value = mock_adoption
        mock_result_animal = MagicMock()
        mock_result_animal.scalar_one_or_none.return_value = mock_animal
        db.execute.side_effect = [mock_result_adoption, mock_result_animal]

        await process_return(db, return_req.id)

        assert mock_animal.status == "medical_hold"


# -- get_return_request --


class TestGetReturnRequest:
    """Tests for fetching return requests."""

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ReturnNotFoundError):
            await get_return_request(db, uuid4())

    @pytest.mark.asyncio
    async def test_returns_request_details(self) -> None:
        return_id = uuid4()
        return_req = MagicMock()
        return_req.id = return_id
        return_req.adoption_request_id = uuid4()
        return_req.reason = "Allergies"
        return_req.animal_condition = "healthy"
        return_req.is_emergency = False
        return_req.status = "pending"
        return_req.staff_notes = None
        return_req.requested_by = uuid4()
        return_req.requested_at = datetime.now(UTC)
        return_req.completed_at = None

        db = AsyncMock()
        db.get.return_value = return_req

        result = await get_return_request(db, return_id)

        assert result["id"] == return_id
        assert result["reason"] == "Allergies"


# -- list_return_requests --


class TestListReturnRequests:
    """Tests for listing return requests."""

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await list_return_requests(db)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_of_requests(self) -> None:
        r1 = MagicMock()
        r1.id = uuid4()
        r1.adoption_request_id = uuid4()
        r1.reason = "Moving"
        r1.animal_condition = "healthy"
        r1.is_emergency = False
        r1.status = "pending"
        r1.requested_at = datetime.now(UTC)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [r1]
        mock_result.scalars.return_value = mock_scalars
        db.execute.return_value = mock_result

        result = await list_return_requests(db, status_filter="pending")

        assert len(result) == 1
        assert result[0]["reason"] == "Moving"


# -- get_return_analytics --


class TestGetReturnAnalytics:
    """Tests for return analytics."""

    @pytest.mark.asyncio
    async def test_returns_zeros_when_no_data(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        db.execute.return_value = mock_result

        result = await get_return_analytics(db)

        assert result["total_returns"] == 0
        assert result["by_condition"] == {}
        assert result["emergency_count"] == 0
        assert result["emergency_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_returns_analytics(self) -> None:
        # Total count
        mock_total = MagicMock()
        mock_total.scalar_one.return_value = 10

        # By condition
        condition_row1 = MagicMock()
        condition_row1.animal_condition = "healthy"
        condition_row1.count = 7
        condition_row2 = MagicMock()
        condition_row2.animal_condition = "injured"
        condition_row2.count = 3
        mock_condition = MagicMock()
        mock_condition.__iter__ = MagicMock(return_value=iter([condition_row1, condition_row2]))

        # Emergency count
        mock_emergency = MagicMock()
        mock_emergency.scalar_one.return_value = 2

        db = AsyncMock()
        db.execute.side_effect = [mock_total, mock_condition, mock_emergency]

        result = await get_return_analytics(db)

        assert result["total_returns"] == 10
        assert result["by_condition"]["healthy"] == 7
        assert result["by_condition"]["injured"] == 3
        assert result["emergency_count"] == 2
        assert result["emergency_pct"] == 20.0
