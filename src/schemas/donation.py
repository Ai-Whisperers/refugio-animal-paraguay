"""Pydantic schemas for Donor and Donation resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.db.models.donation import CurrencyCode, DonationStatus, PaymentMethod, RecurringInterval


class CurrencyBreakdown(BaseModel):
    """Aggregated totals for a single currency."""

    currency: str
    count: int
    total_amount_cents: int


class StatusBreakdown(BaseModel):
    """Count of donations per status."""

    status: str
    count: int


class PaymentMethodBreakdown(BaseModel):
    """Count and total per payment method."""

    payment_method: str
    count: int
    total_amount_cents: int


class DonationStatsResponse(BaseModel):
    """Aggregated donation statistics for the staff dashboard.

    All totals are scoped to the optional date range supplied in query params.
    """

    total_donations: int
    by_currency: list[CurrencyBreakdown]
    by_status: list[StatusBreakdown]
    by_payment_method: list[PaymentMethodBreakdown]
    date_from: datetime | None = None
    date_to: datetime | None = None


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


class DonorListResponse(DonorResponse):
    """Donor record with donation summary stats for list views."""

    total_donations: int = 0
    total_donated_cents: int = 0


class DonationCreate(BaseModel):
    """Fields for creating a donation record."""

    donor_id: UUID | None = None
    campaign_id: UUID | None = None
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
    stripe_subscription_id: str | None = None
    stripe_customer_id: str | None = None
    is_recurring: bool = False
    recurring_interval: RecurringInterval | None = None
    status: DonationStatus
    fund_category: str | None = None
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


class SepaIntentCreate(BaseModel):
    """Request body for creating a SEPA Direct Debit PaymentIntent."""

    donor_id: UUID
    amount_cents: int = Field(..., gt=0)
    notes: str | None = None


class SepaIntentResponse(BaseModel):
    """Response for SEPA Direct Debit PaymentIntent creation."""

    donation_id: UUID
    stripe_payment_intent_id: str
    client_secret: str
    amount_cents: int
    currency: CurrencyCode = CurrencyCode.EUR


class SubscriptionCreate(BaseModel):
    """Request body for creating a recurring donation subscription."""

    donor_id: UUID
    amount_cents: int = Field(..., gt=0)
    currency: CurrencyCode = CurrencyCode.EUR
    interval: RecurringInterval = RecurringInterval.MONTH
    payment_method_id: str = Field(
        ..., description="Stripe payment method ID (pm_...) attached to the customer"
    )
    notes: str | None = None


class SubscriptionResponse(BaseModel):
    """Response for a created subscription."""

    donation_id: UUID
    stripe_subscription_id: str
    stripe_customer_id: str
    amount_cents: int
    currency: CurrencyCode
    interval: RecurringInterval
    status: str


class SubscriptionCancelResponse(BaseModel):
    """Response for subscription cancellation."""

    stripe_subscription_id: str
    status: str
