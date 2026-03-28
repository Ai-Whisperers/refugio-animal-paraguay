"""Unit tests for shift signup API schemas (RAP-182).

Tests the response models used for volunteer self-signup endpoints.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.api.shifts import MySignupsResponse, ShiftSignupResponse


class TestShiftSignupResponse:
    def test_minimal_valid_signup(self) -> None:
        signup_id = uuid4()
        shift_id = uuid4()
        volunteer_id = uuid4()
        now = datetime.now(UTC)
        resp = ShiftSignupResponse(
            id=signup_id,
            shift_id=shift_id,
            volunteer_id=volunteer_id,
            confirmed=False,
            attended=None,
            signed_up_at=now,
            notes=None,
        )
        assert resp.id == signup_id
        assert resp.shift_id == shift_id
        assert resp.volunteer_id == volunteer_id
        assert resp.confirmed is False
        assert resp.attended is None
        assert resp.notes is None

    def test_attended_true(self) -> None:
        resp = ShiftSignupResponse(
            id=uuid4(),
            shift_id=uuid4(),
            volunteer_id=uuid4(),
            confirmed=True,
            attended=True,
            signed_up_at=datetime.now(UTC),
        )
        assert resp.attended is True
        assert resp.confirmed is True

    def test_attended_false_no_show(self) -> None:
        resp = ShiftSignupResponse(
            id=uuid4(),
            shift_id=uuid4(),
            volunteer_id=uuid4(),
            confirmed=True,
            attended=False,
            signed_up_at=datetime.now(UTC),
        )
        assert resp.attended is False

    def test_notes_populated(self) -> None:
        resp = ShiftSignupResponse(
            id=uuid4(),
            shift_id=uuid4(),
            volunteer_id=uuid4(),
            confirmed=False,
            signed_up_at=datetime.now(UTC),
            notes="Will arrive 10 minutes late",
        )
        assert resp.notes == "Will arrive 10 minutes late"

    def test_uuid_fields_are_uuids(self) -> None:
        signup_id = UUID("12345678-1234-5678-1234-567812345678")
        resp = ShiftSignupResponse(
            id=signup_id,
            shift_id=uuid4(),
            volunteer_id=uuid4(),
            confirmed=False,
            signed_up_at=datetime.now(UTC),
        )
        assert isinstance(resp.id, UUID)
        assert resp.id == signup_id

    def test_from_attributes_config(self) -> None:
        assert ShiftSignupResponse.model_config.get("from_attributes") is True


class TestMySignupsResponse:
    def test_empty_response(self) -> None:
        resp = MySignupsResponse(items=[], total=0)
        assert resp.items == []
        assert resp.total == 0

    def test_response_with_items(self) -> None:
        now = datetime.now(UTC)
        signup = ShiftSignupResponse(
            id=uuid4(),
            shift_id=uuid4(),
            volunteer_id=uuid4(),
            confirmed=False,
            signed_up_at=now,
        )
        resp = MySignupsResponse(items=[signup], total=1)
        assert len(resp.items) == 1
        assert resp.total == 1

    def test_total_count_reflects_items(self) -> None:
        now = datetime.now(UTC)
        signups = [
            ShiftSignupResponse(
                id=uuid4(),
                shift_id=uuid4(),
                volunteer_id=uuid4(),
                confirmed=False,
                signed_up_at=now,
            )
            for _ in range(3)
        ]
        resp = MySignupsResponse(items=signups, total=3)
        assert resp.total == 3
        assert len(resp.items) == 3
