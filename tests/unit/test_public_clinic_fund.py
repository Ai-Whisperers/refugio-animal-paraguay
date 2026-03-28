"""Unit tests for public clinic fund schemas and endpoint logic.

Tests cover:
  - ClinicFundRequest validation (amount, currency, names, email)
  - ClinicFundResponse field population
  - PublicClinicSummary / PublicClinicDetail validation
  - ClinicFundingStats field coercion
"""

import pytest
from pydantic import ValidationError
from src.api.public_clinic_fund import (
    MINIMUM_DONATION_CENTS,
    ClinicFundingStats,
    ClinicFundRequest,
    ClinicFundResponse,
    PublicClinicDetail,
    PublicClinicListResponse,
    PublicClinicSummary,
    PublicServiceSummary,
)

# ---------------------------------------------------------------------------
# ClinicFundRequest
# ---------------------------------------------------------------------------


class TestClinicFundRequest:
    """Validation for the clinic fund donation request schema."""

    def test_valid_request(self) -> None:
        req = ClinicFundRequest(
            clinic_id="abc-123",
            amount_cents=2000,
            currency="EUR",
            donor_name="Maria Garcia",
            donor_email="maria@example.com",
        )
        assert req.amount_cents == 2000
        assert req.currency == "EUR"
        assert req.service_id is None
        assert req.message is None

    def test_valid_with_service_and_message(self) -> None:
        req = ClinicFundRequest(
            clinic_id="abc-123",
            amount_cents=5000,
            currency="EUR",
            service_id="svc-456",
            donor_name="Pedro Lopez",
            donor_email="pedro@example.com",
            message="For castrations",
        )
        assert req.service_id == "svc-456"
        assert req.message == "For castrations"

    def test_rejects_below_minimum_amount(self) -> None:
        with pytest.raises((ValueError, ValidationError)):
            ClinicFundRequest(
                clinic_id="abc",
                amount_cents=MINIMUM_DONATION_CENTS - 1,
                currency="EUR",
                donor_name="Test User",
                donor_email="test@example.com",
            )

    def test_rejects_non_eur_currency(self) -> None:
        with pytest.raises((ValueError, ValidationError)):
            ClinicFundRequest(
                clinic_id="abc",
                amount_cents=2000,
                currency="USD",
                donor_name="Test User",
                donor_email="test@example.com",
            )

    def test_rejects_empty_donor_name(self) -> None:
        with pytest.raises((ValueError, ValidationError)):
            ClinicFundRequest(
                clinic_id="abc",
                amount_cents=2000,
                currency="EUR",
                donor_name="",
                donor_email="test@example.com",
            )

    def test_rejects_invalid_email(self) -> None:
        with pytest.raises((ValueError, ValidationError)):
            ClinicFundRequest(
                clinic_id="abc",
                amount_cents=2000,
                currency="EUR",
                donor_name="Test User",
                donor_email="not-an-email",
            )

    def test_currency_uppercased(self) -> None:
        req = ClinicFundRequest(
            clinic_id="abc",
            amount_cents=1000,
            currency="eur",
            donor_name="Test User",
            donor_email="test@example.com",
        )
        assert req.currency == "EUR"

    def test_minimum_amount_accepted(self) -> None:
        req = ClinicFundRequest(
            clinic_id="abc",
            amount_cents=MINIMUM_DONATION_CENTS,
            currency="EUR",
            donor_name="Test User",
            donor_email="test@example.com",
        )
        assert req.amount_cents == MINIMUM_DONATION_CENTS


# ---------------------------------------------------------------------------
# ClinicFundResponse
# ---------------------------------------------------------------------------


class TestClinicFundResponse:
    """Validation for the clinic fund donation response schema."""

    def test_full_response(self) -> None:
        resp = ClinicFundResponse(
            donation_id="don-123",
            clinic_name="Clinica Vida",
            donor_email="donor@example.com",
            amount_cents=5000,
            currency="EUR",
            service_name="Castration",
            stripe_checkout_url="https://checkout.stripe.com/pay/cs_test_123",
            message="Thank you!",
        )
        assert resp.donation_id == "don-123"
        assert resp.service_name == "Castration"
        assert resp.stripe_checkout_url is not None

    def test_response_without_stripe(self) -> None:
        resp = ClinicFundResponse(
            donation_id="don-456",
            clinic_name="Clinica Sol",
            donor_email="donor@example.com",
            amount_cents=1000,
            currency="EUR",
            service_name=None,
            stripe_checkout_url=None,
            message="Thank you!",
        )
        assert resp.stripe_checkout_url is None
        assert resp.service_name is None

    def test_response_with_service_no_stripe(self) -> None:
        resp = ClinicFundResponse(
            donation_id="don-789",
            clinic_name="Clinica Luna",
            donor_email="donor@example.com",
            amount_cents=3000,
            currency="EUR",
            service_name="Vaccination",
            stripe_checkout_url=None,
            message="Donation recorded",
        )
        assert resp.service_name == "Vaccination"


# ---------------------------------------------------------------------------
# PublicClinicSummary
# ---------------------------------------------------------------------------


class TestPublicClinicSummary:
    """Validation for the public clinic summary schema."""

    def test_basic_summary(self) -> None:
        summary = PublicClinicSummary(
            id="clinic-1",
            name="Clinica Vida",
            city="Asuncion",
            department="Central",
            specialties="Surgery, Dental",
            accepts_emergencies=True,
        )
        assert summary.name == "Clinica Vida"
        assert summary.accepts_emergencies is True

    def test_minimal_summary(self) -> None:
        summary = PublicClinicSummary(
            id="clinic-2",
            name="Clinica Sol",
            city="Luque",
        )
        assert summary.department is None
        assert summary.specialties is None
        assert summary.accepts_emergencies is False


# ---------------------------------------------------------------------------
# PublicClinicDetail
# ---------------------------------------------------------------------------


class TestPublicClinicDetail:
    """Validation for the public clinic detail schema."""

    def test_detail_with_services(self) -> None:
        detail = PublicClinicDetail(
            id="clinic-1",
            name="Clinica Vida",
            city="Asuncion",
            address="Av. Mcal Lopez 1234",
            phone="+595 21 123456",
            email="info@clinicavida.com",
            services=[
                PublicServiceSummary(
                    id="svc-1",
                    name="Castration",
                    category="surgery",
                    price_eur=30.0,
                ),
            ],
        )
        assert len(detail.services) == 1
        assert detail.services[0].name == "Castration"

    def test_detail_empty_services(self) -> None:
        detail = PublicClinicDetail(
            id="clinic-2",
            name="Clinica Sol",
            city="Luque",
            address="Calle 1",
            phone="+595 21 654321",
            email="sol@example.com",
        )
        assert detail.services == []


# ---------------------------------------------------------------------------
# PublicClinicListResponse
# ---------------------------------------------------------------------------


class TestPublicClinicListResponse:
    """Validation for the paginated clinic list response."""

    def test_list_response(self) -> None:
        resp = PublicClinicListResponse(
            items=[
                PublicClinicSummary(id="c1", name="A", city="X"),
                PublicClinicSummary(id="c2", name="B", city="Y"),
            ],
            total=2,
            page=1,
            page_size=20,
        )
        assert len(resp.items) == 2
        assert resp.total == 2


# ---------------------------------------------------------------------------
# ClinicFundingStats
# ---------------------------------------------------------------------------


class TestClinicFundingStats:
    """Validation for the clinic funding stats schema."""

    def test_stats_with_data(self) -> None:
        stats = ClinicFundingStats(
            clinic_id="clinic-1",
            clinic_name="Clinica Vida",
            total_funded_cents=150000,
            donation_count=42,
        )
        assert stats.total_funded_cents == 150000
        assert stats.donation_count == 42
        assert stats.currency == "EUR"

    def test_stats_empty(self) -> None:
        stats = ClinicFundingStats(
            clinic_id="clinic-2",
            clinic_name="New Clinic",
        )
        assert stats.total_funded_cents == 0
        assert stats.donation_count == 0


# ---------------------------------------------------------------------------
# PublicServiceSummary
# ---------------------------------------------------------------------------


class TestPublicServiceSummary:
    """Validation for the public service summary schema."""

    def test_full_service(self) -> None:
        svc = PublicServiceSummary(
            id="svc-1",
            name="Castration",
            description="Standard castration for dogs and cats",
            category="surgery",
            price_eur=30.0,
        )
        assert svc.price_eur == 30.0

    def test_service_no_price(self) -> None:
        svc = PublicServiceSummary(
            id="svc-2",
            name="Consultation",
            category="consultation",
        )
        assert svc.price_eur is None
        assert svc.description is None
