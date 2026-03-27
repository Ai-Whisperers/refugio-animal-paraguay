"""Pydantic schemas for recurring donation subscriptions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.db.models.donation import CurrencyCode, RecurringInterval


class SubscriptionCreateRequest(BaseModel):
    """Request body for creating a recurring donation subscription."""

    donor_id: UUID
    amount_cents: int = Field(..., gt=0, description="Amount in smallest currency unit")
    currency: CurrencyCode = CurrencyCode.EUR
    interval: RecurringInterval = RecurringInterval.MONTH
    payment_method_id: str = Field(
        ..., description="Stripe payment method ID (pm_...) attached to the customer"
    )
    notes: str | None = None


class SubscriptionDetailResponse(BaseModel):
    """Full subscription detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    donor_id: UUID
    stripe_subscription_id: str
    stripe_customer_id: str
    stripe_price_id: str | None = None
    amount_cents: int
    currency: str
    interval: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    canceled_at: datetime | None = None
    last_payment_error: str | None = None
    failed_payment_count: int = 0
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionListResponse(BaseModel):
    """Paginated list of subscriptions."""

    items: list[SubscriptionDetailResponse]
    total: int
    page: int
    per_page: int


class SubscriptionCancelRequest(BaseModel):
    """Request body for canceling a subscription."""

    cancel_immediately: bool = Field(
        default=False,
        description="If true, cancel immediately. If false, cancel at period end.",
    )
    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Optional cancellation reason",
    )


class SubscriptionUpdateRequest(BaseModel):
    """Request body for updating a subscription (e.g., changing amount)."""

    amount_cents: int | None = Field(default=None, gt=0)
    payment_method_id: str | None = None
    notes: str | None = None


class SubscriptionStatsResponse(BaseModel):
    """Aggregated subscription statistics."""

    total_active: int
    total_paused: int
    total_canceled: int
    total_past_due: int
    monthly_recurring_cents: int
    yearly_recurring_cents: int
    currency: str = "EUR"
