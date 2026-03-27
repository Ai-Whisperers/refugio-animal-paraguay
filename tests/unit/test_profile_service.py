"""Unit tests for the profile management service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.services.profile_service import (
    PREFERENCE_MAP,
    change_password,
    confirm_account_deletion,
    export_user_data,
    get_simple_preferences,
    request_account_deletion,
    update_profile,
    update_simple_preferences,
)


def _make_user(**overrides):
    """Create a mock User object with sensible defaults."""
    user = MagicMock()
    user.id = overrides.get("id", uuid4())
    user.full_name = overrides.get("full_name", "Test User")
    user.email = overrides.get("email", "test@refugio.org")
    user.phone = overrides.get("phone", "+595981234567")
    user.role = overrides.get("role", "adopter")
    user.is_active = overrides.get("is_active", True)
    user.email_verified = overrides.get("email_verified", True)
    user.hashed_password = overrides.get("hashed_password", "$2b$12$hashedvalue")
    user.created_at = overrides.get("created_at", datetime.now(UTC))
    user.updated_at = overrides.get("updated_at", datetime.now(UTC))
    return user


def _make_mock_db():
    """Create a mock async database session."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


class TestUpdateProfile:
    """Tests for update_profile function."""

    @pytest.mark.asyncio()
    async def test_updates_full_name(self) -> None:
        db = _make_mock_db()
        user = _make_user(full_name="Old Name")
        result = await update_profile(db, user, full_name="New Name")
        assert result.full_name == "New Name"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_updates_phone(self) -> None:
        db = _make_mock_db()
        user = _make_user(phone=None)
        result = await update_profile(db, user, phone="+595981999999")
        assert result.phone == "+595981999999"

    @pytest.mark.asyncio()
    async def test_clears_phone_with_empty_string(self) -> None:
        db = _make_mock_db()
        user = _make_user(phone="+595981234567")
        result = await update_profile(db, user, phone="")
        assert result.phone is None

    @pytest.mark.asyncio()
    async def test_does_not_change_unspecified_fields(self) -> None:
        db = _make_mock_db()
        user = _make_user(full_name="Original", phone="+595981234567")
        await update_profile(db, user, full_name="Changed")
        assert user.phone == "+595981234567"


class TestChangePassword:
    """Tests for change_password function."""

    @pytest.mark.asyncio()
    @patch("src.services.profile_service.verify_password")
    @patch("src.services.profile_service.hash_password")
    async def test_changes_password_with_correct_current(
        self, mock_hash, mock_verify
    ) -> None:
        mock_verify.side_effect = lambda plain, hashed: plain == "current123"
        mock_hash.return_value = "$2b$12$newhash"
        db = _make_mock_db()
        user = _make_user()

        result = await change_password(db, user, "current123", "NewPass1!")
        assert result is True
        assert user.hashed_password == "$2b$12$newhash"

    @pytest.mark.asyncio()
    @patch("src.services.profile_service.verify_password")
    async def test_rejects_incorrect_current_password(self, mock_verify) -> None:
        mock_verify.return_value = False
        db = _make_mock_db()
        user = _make_user()

        result = await change_password(db, user, "wrong", "NewPass1!")
        assert result is False

    @pytest.mark.asyncio()
    @patch("src.services.profile_service.verify_password")
    async def test_rejects_same_password(self, mock_verify) -> None:
        # First call checks current, second checks if new == current
        mock_verify.return_value = True
        db = _make_mock_db()
        user = _make_user()

        result = await change_password(db, user, "Same1!", "Same1!")
        assert result is False


class TestGetSimplePreferences:
    """Tests for get_simple_preferences function."""

    @pytest.mark.asyncio()
    async def test_returns_defaults_when_no_preferences_exist(self) -> None:
        db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        prefs = await get_simple_preferences(db, uuid4())
        # All should default to True
        for key in PREFERENCE_MAP:
            assert prefs[key] is True

    @pytest.mark.asyncio()
    async def test_returns_stored_preference_values(self) -> None:
        db = _make_mock_db()
        mock_pref = MagicMock()
        mock_pref.notification_type = "adoption_status_changed"
        mock_pref.channel = "email"
        mock_pref.enabled = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_pref]
        db.execute.return_value = mock_result

        prefs = await get_simple_preferences(db, uuid4())
        assert prefs["email_adoption"] is False


class TestUpdateSimplePreferences:
    """Tests for update_simple_preferences function."""

    @pytest.mark.asyncio()
    async def test_creates_new_preferences(self) -> None:
        db = _make_mock_db()

        mock_empty = MagicMock()
        mock_empty.scalar_one_or_none.return_value = None
        mock_empty.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_empty

        await update_simple_preferences(db, uuid4(), {"email_adoption": False})
        assert db.add.called


class TestExportUserData:
    """Tests for export_user_data function."""

    @pytest.mark.asyncio()
    async def test_exports_user_profile(self) -> None:
        db = _make_mock_db()
        user = _make_user(email="export@test.org")

        mock_empty = MagicMock()
        mock_empty.scalar_one_or_none.return_value = None
        mock_empty.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_empty

        data = await export_user_data(db, user)

        assert data["user_profile"]["email"] == "export@test.org"
        assert data["adoption_requests"] == []
        assert data["donations"] == []
        assert data["sponsorships"] == []
        assert "export_date" in data

    @pytest.mark.asyncio()
    async def test_export_includes_all_sections(self) -> None:
        db = _make_mock_db()
        user = _make_user()

        mock_empty = MagicMock()
        mock_empty.scalar_one_or_none.return_value = None
        mock_empty.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_empty

        data = await export_user_data(db, user)
        expected_keys = {
            "export_date",
            "user_profile",
            "adoption_requests",
            "donations",
            "sponsorships",
            "notification_preferences",
            "consents",
        }
        assert set(data.keys()) == expected_keys


class TestRequestAccountDeletion:
    """Tests for request_account_deletion function."""

    @pytest.mark.asyncio()
    @patch("src.services.profile_service.verify_password")
    async def test_returns_none_for_wrong_password(self, mock_verify) -> None:
        mock_verify.return_value = False
        db = _make_mock_db()
        user = _make_user()

        result = await request_account_deletion(db, user, "wrongpass")
        assert result is None

    @pytest.mark.asyncio()
    @patch("src.services.profile_service.verify_password")
    async def test_creates_token_for_correct_password(self, mock_verify) -> None:
        mock_verify.return_value = True
        db = _make_mock_db()
        user = _make_user()

        mock_empty = MagicMock()
        mock_empty.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_empty

        token = await request_account_deletion(db, user, "correct")
        assert token is not None
        assert len(token) > 20
        assert db.add.called


class TestConfirmAccountDeletion:
    """Tests for confirm_account_deletion function."""

    @pytest.mark.asyncio()
    async def test_returns_false_for_invalid_token(self) -> None:
        db = _make_mock_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await confirm_account_deletion(db, "bogus-token")
        assert result is False

    @pytest.mark.asyncio()
    async def test_returns_false_for_expired_token(self) -> None:
        db = _make_mock_db()
        mock_token = MagicMock()
        mock_token.expires_at = datetime.now(UTC) - timedelta(hours=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        db.execute.return_value = mock_result

        result = await confirm_account_deletion(db, "expired-token")
        assert result is False

    @pytest.mark.asyncio()
    async def test_anonymizes_user_on_valid_token(self) -> None:
        db = _make_mock_db()
        user_id = uuid4()

        mock_token = MagicMock()
        mock_token.expires_at = datetime.now(UTC) + timedelta(hours=12)
        mock_token.user_id = user_id

        mock_user = _make_user(id=user_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_token
        db.execute.return_value = mock_result
        db.get.return_value = mock_user

        result = await confirm_account_deletion(db, "valid-token")

        assert result is True
        assert mock_user.full_name == "Deleted User"
        assert "deleted+" in mock_user.email
        assert mock_user.phone is None
        assert mock_user.is_active is False
