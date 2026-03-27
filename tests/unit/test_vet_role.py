"""Unit tests for vet role and permission dependencies."""

from src.db.models.user import UserRole


class TestUserRoleEnum:
    """Tests for UserRole enum including vet role."""

    def test_vet_role_exists(self) -> None:
        assert UserRole.VET == "vet"

    def test_staff_role_exists(self) -> None:
        assert UserRole.STAFF == "staff"

    def test_admin_role_exists(self) -> None:
        assert UserRole.ADMIN == "admin"

    def test_all_roles(self) -> None:
        roles = {r.value for r in UserRole}
        assert roles == {"staff", "admin", "vet"}

    def test_vet_role_string_value(self) -> None:
        assert str(UserRole.VET) == "vet"
