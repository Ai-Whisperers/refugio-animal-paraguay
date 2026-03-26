"""Shared test data factories for refugio-animal-paraguay.

Use these factories across unit and integration tests to create
consistent, valid test data. Each factory returns a dict suitable
for the corresponding API endpoint or model constructor.

Usage:
    from tests.factories import AnimalFactory, AdopterFactory

    animal = AnimalFactory.build()
    animal_custom = AnimalFactory.build(name="Luna", species="cat")
"""

import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar


class _BaseFactory:
    """Base factory with build() class method that merges defaults with overrides."""

    _defaults: ClassVar[dict[str, Any]] = {}

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        """Create a dict of test data, merging defaults with overrides."""
        data = cls._defaults.copy()
        data.update(overrides)
        return data

    @classmethod
    def build_many(cls, count: int, **shared_overrides: Any) -> list[dict[str, Any]]:
        """Create multiple instances with unique emails/IDs."""
        return [cls.build(**shared_overrides) for _ in range(count)]


class AnimalFactory(_BaseFactory):
    """Factory for animal API payloads."""

    _defaults: ClassVar[dict[str, Any]] = {
        "name": "Firulais",
        "species": "dog",
        "breed": "mixed",
        "age_months": 24,
        "sex": "male",
        "status": "available",
        "description": "Friendly mixed-breed dog found near Asuncion.",
    }

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        data = super().build(**overrides)
        if "name" not in overrides:
            data["name"] = f"Animal-{uuid.uuid4().hex[:6]}"
        return data


class AdopterFactory(_BaseFactory):
    """Factory for adopter API payloads."""

    _defaults: ClassVar[dict[str, Any]] = {
        "full_name": "Maria Garcia",
        "phone": "+595981234567",
        "address": "Asuncion, Paraguay",
        "gdpr_consent": True,
    }

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        data = super().build(**overrides)
        if "email" not in overrides:
            data["email"] = f"adopter-{uuid.uuid4().hex[:8]}@example.com"
        return data


class DonorFactory(_BaseFactory):
    """Factory for donor API payloads."""

    _defaults: ClassVar[dict[str, Any]] = {
        "full_name": "Jan de Vries",
        "country": "NL",
        "currency": "EUR",
        "gdpr_consent": True,
    }

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        data = super().build(**overrides)
        if "email" not in overrides:
            data["email"] = f"donor-{uuid.uuid4().hex[:8]}@example.nl"
        return data


class DonationFactory(_BaseFactory):
    """Factory for donation API payloads."""

    _defaults: ClassVar[dict[str, Any]] = {
        "amount_cents": 5000,
        "currency": "EUR",
        "payment_method": "card",
    }

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        data = super().build(**overrides)
        if "donor_id" not in overrides:
            data["donor_id"] = str(uuid.uuid4())
        return data


class IntakeFactory(_BaseFactory):
    """Factory for animal intake API payloads."""

    _defaults: ClassVar[dict[str, Any]] = {
        "name": "Rescatado",
        "species": "dog",
        "source": "stray",
        "location_found": "Plaza de Armas, Asuncion",
        "finder_name": "Carlos Lopez",
        "finder_phone": "+595971234567",
        "condition_on_arrival": "Mild dehydration, no visible injuries",
        "requires_quarantine": False,
    }


class UserFactory(_BaseFactory):
    """Factory for user creation (internal, not API)."""

    _defaults: ClassVar[dict[str, Any]] = {
        "role": "staff",
        "is_active": True,
    }

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        data = super().build(**overrides)
        if "id" not in overrides:
            data["id"] = str(uuid.uuid4())
        if "email" not in overrides:
            data["email"] = f"user-{uuid.uuid4().hex[:8]}@refugio.test"
        if "password" not in overrides:
            data["password"] = "TestPass123!"
        return data


class VerificationTokenFactory(_BaseFactory):
    """Factory for email verification / password reset tokens."""

    _defaults: ClassVar[dict[str, Any]] = {
        "token_type": "email_verification",
    }

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        data = super().build(**overrides)
        if "user_id" not in overrides:
            data["user_id"] = str(uuid.uuid4())
        if "token" not in overrides:
            import secrets

            data["token"] = secrets.token_urlsafe(32)
        if "expires_at" not in overrides:
            from datetime import timedelta

            data["expires_at"] = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
        return data
