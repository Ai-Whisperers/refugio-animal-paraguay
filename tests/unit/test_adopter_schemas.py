"""Unit tests for src/schemas/adopter.py."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.schemas.adopter import AdopterCreate, AdopterResponse, AdopterUpdate


class TestAdopterCreate:
    def test_minimal_valid_payload(self) -> None:
        a = AdopterCreate(full_name="Juan Pérez", email="juan@example.com")
        assert a.full_name == "Juan Pérez"
        assert a.email == "juan@example.com"
        assert a.phone is None
        assert a.address is None
        assert a.gdpr_consent_at is None

    def test_all_fields(self) -> None:
        now = datetime.now(UTC)
        a = AdopterCreate(
            full_name="Ana García",
            email="ana@example.com",
            phone="+595 21 555 1234",
            address="Calle Principal 123, Asunción",
            gdpr_consent_at=now,
        )
        assert a.phone == "+595 21 555 1234"
        assert a.address == "Calle Principal 123, Asunción"
        assert a.gdpr_consent_at == now

    def test_full_name_cannot_be_empty(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            AdopterCreate(full_name="", email="x@example.com")

    def test_full_name_cannot_exceed_255_chars(self) -> None:
        with pytest.raises(ValidationError, match="string_too_long"):
            AdopterCreate(full_name="x" * 256, email="x@example.com")

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdopterCreate(full_name="Juan", email="not-an-email")

    def test_phone_cannot_exceed_50_chars(self) -> None:
        with pytest.raises(ValidationError, match="string_too_long"):
            AdopterCreate(full_name="Juan", email="j@example.com", phone="x" * 51)

    def test_phone_at_exactly_50_chars_is_valid(self) -> None:
        a = AdopterCreate(full_name="Juan", email="j@example.com", phone="x" * 50)
        assert len(a.phone) == 50  # type: ignore[arg-type]

    def test_email_domain_is_normalised_to_lowercase(self) -> None:
        # Pydantic normalises the domain part only; local part is case-preserved.
        a = AdopterCreate(full_name="Juan", email="JUAN@EXAMPLE.COM")
        assert a.email == "JUAN@example.com"


class TestAdopterUpdate:
    def test_empty_payload_is_valid(self) -> None:
        u = AdopterUpdate()
        assert u.full_name is None
        assert u.phone is None
        assert u.address is None
        assert u.gdpr_consent_at is None

    def test_partial_phone_only(self) -> None:
        u = AdopterUpdate(phone="+595981234567")
        assert u.phone == "+595981234567"
        assert u.full_name is None

    def test_model_dump_exclude_unset_only_returns_provided_fields(self) -> None:
        u = AdopterUpdate(address="New Address 456")
        data = u.model_dump(exclude_unset=True)
        assert data == {"address": "New Address 456"}
        assert "full_name" not in data
        assert "phone" not in data

    def test_full_name_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="string_too_short"):
            AdopterUpdate(full_name="")

    def test_gdpr_consent_at_can_be_set(self) -> None:
        now = datetime.now(UTC)
        u = AdopterUpdate(gdpr_consent_at=now)
        data = u.model_dump(exclude_unset=True)
        assert data == {"gdpr_consent_at": now}


class TestAdopterResponse:
    def test_from_orm_attributes(self) -> None:
        now = datetime.now(UTC)
        uid = uuid4()

        class _FakeAdopter:
            id = uid
            full_name = "Pedro López"
            email = "pedro@example.com"
            phone = None
            address = None
            gdpr_consent_at = None
            created_at = now
            updated_at = now

        resp = AdopterResponse.model_validate(_FakeAdopter())
        assert resp.id == uid
        assert resp.full_name == "Pedro López"
        assert resp.email == "pedro@example.com"
        assert resp.phone is None
        assert resp.gdpr_consent_at is None

    def test_deleted_at_not_in_response(self) -> None:
        """deleted_at is intentionally excluded from the response schema."""
        assert not hasattr(AdopterResponse.model_fields, "deleted_at")
        assert "deleted_at" not in AdopterResponse.model_fields
