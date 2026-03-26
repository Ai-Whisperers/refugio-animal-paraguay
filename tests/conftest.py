"""Root conftest — shared fixtures available to ALL tests (unit + integration).

Provides lightweight factories and helpers that don't require a database.
Database-dependent fixtures live in tests/integration/conftest.py.
"""

import uuid
from datetime import UTC, datetime

import pytest

# ---------------------------------------------------------------------------
# Deterministic IDs for reproducible tests
# ---------------------------------------------------------------------------
TEST_STAFF_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
TEST_ADOPTER_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")


# ---------------------------------------------------------------------------
# Factories — lightweight dict builders for test data
# ---------------------------------------------------------------------------
def make_animal_data(**overrides: object) -> dict:
    """Return a dict suitable for POST /animals."""
    defaults: dict = {
        "name": "Firulais",
        "species": "dog",
        "breed": "mixed",
        "age_months": 24,
        "sex": "male",
        "status": "available",
        "description": "Friendly mixed-breed dog found near Asuncion.",
    }
    defaults.update(overrides)
    return defaults


def make_adopter_data(**overrides: object) -> dict:
    """Return a dict suitable for POST /adopters."""
    defaults: dict = {
        "full_name": "Maria Garcia",
        "email": f"maria-{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+595981234567",
        "address": "Asuncion, Paraguay",
        "gdpr_consent": True,
    }
    defaults.update(overrides)
    return defaults


def make_donor_data(**overrides: object) -> dict:
    """Return a dict suitable for POST /donors."""
    defaults: dict = {
        "full_name": "Jan de Vries",
        "email": f"jan-{uuid.uuid4().hex[:8]}@example.nl",
        "country": "NL",
        "currency": "EUR",
        "gdpr_consent": True,
    }
    defaults.update(overrides)
    return defaults


def make_intake_data(**overrides: object) -> dict:
    """Return a dict suitable for POST /animals/intake."""
    defaults: dict = {
        "name": "Rescatado",
        "species": "dog",
        "source": "stray",
        "location_found": "Plaza de Armas, Asuncion",
        "finder_name": "Carlos Lopez",
        "finder_phone": "+595971234567",
        "condition_on_arrival": "Mild dehydration, no visible injuries",
        "requires_quarantine": False,
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------
@pytest.fixture
def frozen_now() -> datetime:
    """A fixed UTC datetime for deterministic timestamp tests."""
    return datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC)
