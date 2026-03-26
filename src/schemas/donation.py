"""Pydantic schemas for Donor and Donation resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.db.models.donation import CurrencyCode, DonationStatus, PaymentMethod


class DonorCreate(BaseModel):
    """Fields for creating a donor profile."""

    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    country: str | None = Field(default=None, min_length=2, max_length=2)
    currency_preference: CurrencyCode = CurrencyCode.EUR
    gdpr_consent_at: datetime | None = None


class DonorResponse(BaseModel):
    """Shape returned for a donor record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str
    country: str | None
    currency_preference: CurrencyCode
    gdpr_consent_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DonationCreate(BaseModel):
    """Fields for creating a donation record."""

    donor_id: UUID | None = None
    # Amount in smallest currency unit (cents for EUR/USD, guaraníes for PYG)
    amount_cents: int = Field(..., gt=0)
    currency: CurrencyCode = CurrencyCode.EUR
    payment_method: PaymentMethod = PaymentMethod.STRIPE
    notes: str | None = None


class CashDonationCreate(BaseModel):
    """Fields for recording a cash donation received at the shelter."""

    donor_id: UUID | None = None
    # Amount in smallest currency unit (cents for EUR/USD, guaranies for PYG)
    amount_cents: int = Field(..., gt=0)
    currency: CurrencyCode = CurrencyCode.PYG
    # Paper receipt reference from physical receipt book
    receipt_number: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class DonationResponse(BaseModel):
    """Shape returned for a donation record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donor_id: UUID | None
    amount_cents: int
    currency: CurrencyCode
    payment_method: PaymentMethod
    stripe_payment_intent_id: str | None
    status: DonationStatus
    receipt_number: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class StripeIntentResponse(BaseModel):
    """Stripe PaymentIntent creation response."""

    donation_id: UUID
    stripe_payment_intent_id: str
    client_secret: str
    amount_cents: int
    currency: CurrencyCode
