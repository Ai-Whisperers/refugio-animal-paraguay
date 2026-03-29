"""Unit tests for foster supply request service (RAP-194)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.foster_supply_service import (
    create_supply_request,
    fulfill_request,
    list_all_requests,
    list_requests_for_foster,
    reject_request,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(status: str = "pending") -> MagicMock:
    r = MagicMock()
    r.id = uuid4()
    r.foster_profile_id = uuid4()
    r.placement_id = None
    r.supply_type = "food"
    r.description = "Dog food for two weeks."
    r.quantity = 2
    r.status = status
    r.resolved_at = None
    r.resolved_by = None
    r.staff_notes = None
    r.created_at = None
    r.updated_at = None
    return r


def _make_db_scalar(scalar_value: object) -> AsyncMock:
    """DB that returns a single scalar from execute → scalar_one_or_none."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = scalar_value
    db.execute.return_value = mock_result
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _make_paginated_db(items: list, total: int) -> AsyncMock:
    """DB that returns count then items from successive execute() calls."""
    db = AsyncMock()

    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    items_result = MagicMock()
    items_result.scalars.return_value.all.return_value = items

    db.execute.side_effect = [count_result, items_result]
    return db


# ---------------------------------------------------------------------------
# create_supply_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_supply_request_commits_and_refreshes() -> None:
    """create_supply_request adds the object, commits, and refreshes."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    profile_id = uuid4()
    result = await create_supply_request(
        db,
        foster_profile_id=profile_id,
        supply_type="food",
        description="Ten kilos of dry dog food needed.",
        quantity=10,
    )

    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once()
    # Result is the object passed to db.add
    assert result is db.add.call_args[0][0]


@pytest.mark.asyncio
async def test_create_supply_request_without_placement_id() -> None:
    """placement_id defaults to None when not provided."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    await create_supply_request(
        db,
        foster_profile_id=uuid4(),
        supply_type="medication",
        description="Anti-parasite medication for the cat.",
    )

    added_obj = db.add.call_args[0][0]
    assert added_obj.placement_id is None
    assert added_obj.quantity is None


# ---------------------------------------------------------------------------
# list_requests_for_foster
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_requests_for_foster_returns_items_and_total() -> None:
    """list_requests_for_foster returns the paginated result and total count."""
    mock_item = _make_request()
    db = _make_paginated_db(items=[mock_item], total=1)

    items, total = await list_requests_for_foster(db, foster_profile_id=uuid4())

    assert total == 1
    assert len(items) == 1
    assert items[0] is mock_item


@pytest.mark.asyncio
async def test_list_requests_for_foster_empty() -> None:
    """Returns empty list and zero total when no requests exist."""
    db = _make_paginated_db(items=[], total=0)

    items, total = await list_requests_for_foster(db, foster_profile_id=uuid4())

    assert total == 0
    assert items == []


# ---------------------------------------------------------------------------
# list_all_requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_all_requests_returns_items_and_total() -> None:
    """list_all_requests returns paginated items with total count."""
    mock_items = [_make_request(), _make_request(status="fulfilled")]
    db = _make_paginated_db(items=mock_items, total=2)

    items, total = await list_all_requests(db)

    assert total == 2
    assert len(items) == 2


# ---------------------------------------------------------------------------
# fulfill_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fulfill_request_sets_status_fulfilled() -> None:
    """fulfill_request updates status to fulfilled and records resolver."""
    req = _make_request(status="pending")
    db = _make_db_scalar(req)

    staff_id = uuid4()
    result = await fulfill_request(db, req.id, resolved_by=staff_id, staff_notes="Delivered!")

    assert req.status == "fulfilled"
    assert req.resolved_by == staff_id
    assert req.resolved_at is not None
    assert req.staff_notes == "Delivered!"
    db.commit.assert_awaited_once()
    assert result is req


@pytest.mark.asyncio
async def test_fulfill_request_raises_when_not_found() -> None:
    """ValueError raised with 'not found' when request does not exist."""
    db = _make_db_scalar(None)

    with pytest.raises(ValueError, match="not found"):
        await fulfill_request(db, uuid4(), resolved_by=uuid4())


@pytest.mark.asyncio
async def test_fulfill_request_raises_when_already_fulfilled() -> None:
    """ValueError raised when request is already fulfilled."""
    req = _make_request(status="fulfilled")
    db = _make_db_scalar(req)

    with pytest.raises(ValueError, match="already fulfilled"):
        await fulfill_request(db, req.id, resolved_by=uuid4())


@pytest.mark.asyncio
async def test_fulfill_request_raises_when_rejected() -> None:
    """ValueError raised when request has been rejected."""
    req = _make_request(status="rejected")
    db = _make_db_scalar(req)

    with pytest.raises(ValueError, match="rejected"):
        await fulfill_request(db, req.id, resolved_by=uuid4())


# ---------------------------------------------------------------------------
# reject_request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_request_sets_status_rejected() -> None:
    """reject_request updates status to rejected and records resolver."""
    req = _make_request(status="pending")
    db = _make_db_scalar(req)

    staff_id = uuid4()
    result = await reject_request(db, req.id, resolved_by=staff_id, staff_notes="Out of stock.")

    assert req.status == "rejected"
    assert req.resolved_by == staff_id
    assert req.staff_notes == "Out of stock."
    db.commit.assert_awaited_once()
    assert result is req


@pytest.mark.asyncio
async def test_reject_request_raises_when_not_found() -> None:
    """ValueError raised with 'not found' when request does not exist."""
    db = _make_db_scalar(None)

    with pytest.raises(ValueError, match="not found"):
        await reject_request(db, uuid4(), resolved_by=uuid4())


@pytest.mark.asyncio
async def test_reject_request_raises_when_already_rejected() -> None:
    """ValueError raised when request is already rejected."""
    req = _make_request(status="rejected")
    db = _make_db_scalar(req)

    with pytest.raises(ValueError, match="already rejected"):
        await reject_request(db, req.id, resolved_by=uuid4())


@pytest.mark.asyncio
async def test_reject_request_raises_when_already_fulfilled() -> None:
    """ValueError raised when request is already fulfilled (cannot reverse)."""
    req = _make_request(status="fulfilled")
    db = _make_db_scalar(req)

    with pytest.raises(ValueError, match="fulfilled"):
        await reject_request(db, req.id, resolved_by=uuid4())
