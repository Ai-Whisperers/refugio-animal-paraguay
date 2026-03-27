"""Unit tests for PublicUserRegister schema validation.

Tests cover: valid/invalid emails, phone formats, password strength
requirements, name validation, role validation, and edge cases.
"""

import pytest
from pydantic import ValidationError
from src.schemas.user import PublicUserRegister

# ---------------------------------------------------------------------------
# Valid registration data factory
# ---------------------------------------------------------------------------


def _valid_data(**overrides: object) -> dict:
    """Return a valid registration payload with optional overrides."""
    defaults: dict = {
        "full_name": "Maria Garcia",
        "email": "maria@example.com",
        "phone": "+595981234567",
        "password": "SecureP@ss1",
        "role": "adopter",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestValidRegistration:
    """Valid registration payloads should parse without error."""

    def test_valid_adopter_registration(self) -> None:
        user = PublicUserRegister(**_valid_data(role="adopter"))
        assert user.role == "adopter"
        assert user.full_name == "Maria Garcia"

    def test_valid_donor_registration(self) -> None:
        user = PublicUserRegister(**_valid_data(role="donor"))
        assert user.role == "donor"

    def test_valid_volunteer_registration(self) -> None:
        user = PublicUserRegister(**_valid_data(role="volunteer"))
        assert user.role == "volunteer"

    def test_valid_foster_registration(self) -> None:
        user = PublicUserRegister(**_valid_data(role="foster"))
        assert user.role == "foster"

    def test_all_four_public_roles_accepted(self) -> None:
        for role in ("adopter", "donor", "volunteer", "foster"):
            user = PublicUserRegister(**_valid_data(role=role))
            assert user.role == role


# ---------------------------------------------------------------------------
# Full name validation
# ---------------------------------------------------------------------------


class TestFullNameValidation:
    """Name must be 2-100 chars after stripping whitespace."""

    def test_name_stripped_of_whitespace(self) -> None:
        user = PublicUserRegister(**_valid_data(full_name="  Maria Garcia  "))
        assert user.full_name == "Maria Garcia"

    def test_name_too_short_after_strip(self) -> None:
        with pytest.raises(ValidationError, match="at least 2 characters"):
            PublicUserRegister(**_valid_data(full_name="  A  "))

    def test_name_exactly_two_chars(self) -> None:
        user = PublicUserRegister(**_valid_data(full_name="AB"))
        assert user.full_name == "AB"

    def test_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(full_name="A" * 101))

    def test_name_with_special_characters(self) -> None:
        user = PublicUserRegister(**_valid_data(full_name="Maria Jose Garcia-Lopez"))
        assert user.full_name == "Maria Jose Garcia-Lopez"

    def test_name_with_accented_characters(self) -> None:
        user = PublicUserRegister(**_valid_data(full_name="Jose Gonzalez"))
        assert user.full_name == "Jose Gonzalez"

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(full_name=""))


# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------


class TestEmailValidation:
    """Email must be valid RFC format."""

    def test_valid_email(self) -> None:
        user = PublicUserRegister(**_valid_data(email="test@example.com"))
        assert str(user.email) == "test@example.com"

    def test_invalid_email_format(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(email="not-an-email"))

    def test_email_missing_domain(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(email="user@"))

    def test_email_missing_at(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(email="userexample.com"))


# ---------------------------------------------------------------------------
# Phone validation
# ---------------------------------------------------------------------------


class TestPhoneValidation:
    """Phone must match Paraguay format: +595 followed by 9 digits."""

    def test_valid_paraguay_phone(self) -> None:
        user = PublicUserRegister(**_valid_data(phone="+595981234567"))
        assert user.phone == "+595981234567"

    def test_phone_without_plus(self) -> None:
        with pytest.raises(ValidationError, match="Paraguay format"):
            PublicUserRegister(**_valid_data(phone="595981234567"))

    def test_phone_wrong_country_code(self) -> None:
        with pytest.raises(ValidationError, match="Paraguay format"):
            PublicUserRegister(**_valid_data(phone="+1981234567"))

    def test_phone_too_few_digits(self) -> None:
        with pytest.raises(ValidationError, match="Paraguay format"):
            PublicUserRegister(**_valid_data(phone="+59598123456"))

    def test_phone_too_many_digits(self) -> None:
        with pytest.raises(ValidationError, match="Paraguay format"):
            PublicUserRegister(**_valid_data(phone="+5959812345678"))

    def test_phone_with_letters(self) -> None:
        with pytest.raises(ValidationError, match="Paraguay format"):
            PublicUserRegister(**_valid_data(phone="+595abc234567"))

    def test_phone_whitespace_stripped(self) -> None:
        user = PublicUserRegister(**_valid_data(phone="  +595981234567  "))
        assert user.phone == "+595981234567"


# ---------------------------------------------------------------------------
# Password strength validation
# ---------------------------------------------------------------------------


class TestPasswordValidation:
    """Password: min 8 chars, 1 uppercase, 1 number, 1 special char."""

    def test_valid_strong_password(self) -> None:
        user = PublicUserRegister(**_valid_data(password="SecureP@ss1"))
        assert user.password == "SecureP@ss1"

    def test_password_too_short(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(password="Sh@rt1"))

    def test_password_missing_uppercase(self) -> None:
        with pytest.raises(ValidationError, match="uppercase"):
            PublicUserRegister(**_valid_data(password="securep@ss1"))

    def test_password_missing_number(self) -> None:
        with pytest.raises(ValidationError, match="number"):
            PublicUserRegister(**_valid_data(password="SecureP@ss"))

    def test_password_missing_special_char(self) -> None:
        with pytest.raises(ValidationError, match="special"):
            PublicUserRegister(**_valid_data(password="SecurePass1"))

    def test_password_exactly_eight_chars(self) -> None:
        user = PublicUserRegister(**_valid_data(password="Secur@1x"))
        assert len(user.password) == 8

    def test_password_all_requirements_missing(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            PublicUserRegister(**_valid_data(password="abcdefgh"))
        error_text = str(exc_info.value)
        assert "uppercase" in error_text
        assert "number" in error_text
        assert "special" in error_text


# ---------------------------------------------------------------------------
# Role validation
# ---------------------------------------------------------------------------


class TestRoleValidation:
    """Only public roles are accepted; staff/admin/vet are rejected."""

    def test_staff_role_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(role="staff"))

    def test_admin_role_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(role="admin"))

    def test_vet_role_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(role="vet"))

    def test_invalid_role_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PublicUserRegister(**_valid_data(role="superuser"))
