"""Unit tests for the user role management service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.services.user_role_service import (
    ROLE_DESCRIPTIONS,
    ROLE_WELCOME_MESSAGES,
    SELF_ASSIGNABLE_ROLES,
    InvalidRoleError,
    LastRoleError,
    RoleAlreadyAssignedError,
    add_role,
    get_user_roles,
    remove_role,
)


class TestSelfAssignableRoles:
    """Tests for role constants."""

    def test_contains_expected_public_roles(self) -> None:
        assert "adopter" in SELF_ASSIGNABLE_ROLES
        assert "donor" in SELF_ASSIGNABLE_ROLES
        assert "volunteer" in SELF_ASSIGNABLE_ROLES
        assert "foster" in SELF_ASSIGNABLE_ROLES

    def test_excludes_privileged_roles(self) -> None:
        assert "admin" not in SELF_ASSIGNABLE_ROLES
        assert "staff" not in SELF_ASSIGNABLE_ROLES
        assert "vet" not in SELF_ASSIGNABLE_ROLES

    def test_all_roles_have_descriptions(self) -> None:
        for role in SELF_ASSIGNABLE_ROLES:
            assert role in ROLE_DESCRIPTIONS
            assert len(ROLE_DESCRIPTIONS[role]) > 0

    def test_all_roles_have_welcome_messages(self) -> None:
        for role in SELF_ASSIGNABLE_ROLES:
            assert role in ROLE_WELCOME_MESSAGES
            assert len(ROLE_WELCOME_MESSAGES[role]) > 0


class TestGetUserRoles:
    """Tests for getting user roles."""

    @pytest.mark.asyncio()
    async def test_returns_roles_from_junction_table(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [("adopter",), ("volunteer",)]
        db.execute.return_value = MagicMock(scalars=lambda: mock_result)
        # Actually the function uses result.all() not scalars()
        mock_raw = MagicMock()
        mock_raw.all.return_value = [("adopter",), ("volunteer",)]
        db.execute.return_value = mock_raw

        roles = await get_user_roles(db, "user-123")
        assert roles == ["adopter", "volunteer"]

    @pytest.mark.asyncio()
    async def test_falls_back_to_primary_role_when_no_junction_rows(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        db.execute.return_value = mock_result

        mock_user = MagicMock()
        mock_user.role = "adopter"
        db.get.return_value = mock_user

        roles = await get_user_roles(db, "user-123")
        assert roles == ["adopter"]


class TestAddRole:
    """Tests for adding a role."""

    @pytest.mark.asyncio()
    async def test_rejects_non_self_assignable_role(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidRoleError, match="not available"):
            await add_role(db, "user-123", "admin")

    @pytest.mark.asyncio()
    async def test_rejects_staff_role(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidRoleError, match="not available"):
            await add_role(db, "user-123", "staff")

    @pytest.mark.asyncio()
    async def test_rejects_duplicate_role(self) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        # First execute: check for existing -> returns existing
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = MagicMock()
        db.execute.return_value = existing_result

        with pytest.raises(RoleAlreadyAssignedError, match="already have"):
            await add_role(db, "user-123", "volunteer")

    @pytest.mark.asyncio()
    async def test_adds_new_role_successfully(self) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        # First execute: check for existing -> returns None (not assigned)
        no_existing = MagicMock()
        no_existing.scalar_one_or_none.return_value = None

        # _ensure_primary_role_synced check -> returns None (not synced)
        sync_check = MagicMock()
        sync_check.scalar_one_or_none.return_value = None

        # get_user_roles after add
        roles_result = MagicMock()
        roles_result.all.return_value = [("adopter",), ("volunteer",)]

        mock_user = MagicMock()
        mock_user.role = "adopter"
        db.get.return_value = mock_user

        db.execute.side_effect = [no_existing, sync_check, roles_result]

        roles = await add_role(db, "user-123", "volunteer")
        assert "adopter" in roles
        assert "volunteer" in roles
        assert db.add.called


class TestRemoveRole:
    """Tests for removing a role."""

    @pytest.mark.asyncio()
    async def test_rejects_non_self_assignable_role(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidRoleError, match="cannot be removed"):
            await remove_role(db, "user-123", "admin")

    @pytest.mark.asyncio()
    async def test_prevents_removing_last_role(self) -> None:
        db = AsyncMock()
        # get_user_roles returns single role
        single_result = MagicMock()
        single_result.all.return_value = [("adopter",)]
        db.execute.return_value = single_result

        # Fallback path in get_user_roles
        mock_user = MagicMock()
        mock_user.role = "adopter"
        db.get.return_value = mock_user

        with pytest.raises(LastRoleError, match="at least one"):
            await remove_role(db, "user-123", "adopter")

    @pytest.mark.asyncio()
    async def test_rejects_role_user_doesnt_have(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()

        # get_user_roles returns adopter and donor
        roles_result = MagicMock()
        roles_result.all.return_value = [("adopter",), ("donor",)]
        db.execute.return_value = roles_result

        with pytest.raises(InvalidRoleError, match="don't have"):
            await remove_role(db, "user-123", "volunteer")


class TestExceptionMessages:
    """Tests for error classes."""

    def test_invalid_role_error(self) -> None:
        err = InvalidRoleError("bad role")
        assert err.message == "bad role"

    def test_role_already_assigned_error(self) -> None:
        err = RoleAlreadyAssignedError("already have it")
        assert err.message == "already have it"

    def test_last_role_error(self) -> None:
        err = LastRoleError("can't remove")
        assert err.message == "can't remove"
