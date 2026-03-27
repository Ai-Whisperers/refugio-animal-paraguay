"""Pydantic schemas for Tigo Money payment flow.

Schemas cover three interactions:
  1. TigoPaymentInitRequest  — incoming request to start a checkout session
  2. TigoPaymentInitResponse — response with Tigo checkout URL
  3. TigoCallbackRequest     — inbound webhook from Tigo Money after payment
"""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TigoPaymentInitRequest(BaseModel):
    """Request body to initiate a Tigo Money checkout session."""

    donor_id: UUID = Field(..., description="Existing donor account ID")
    amount_pyg: int = Field(
        ...,
        gt=0,
        description="Donation amount in Paraguayan guaraníes (integer, no decimals)",
    )
    fund_category: str = Field(
        default="general",
        description="Fund allocation category (general, medical, food, shelter)",
    )
    campaign_id: UUID | None = Field(
        default=None,
        description="Optional campaign this donation should be associated with",
    )
    return_url: str = Field(
        ...,
        description="URL to redirect donor to after Tigo payment completes or fails",
    )

    @field_validator("amount_pyg")
    @classmethod
    def amount_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("amount_pyg must be greater than 0")
        return value


class TigoPaymentInitResponse(BaseModel):
    """Response returned to the client after creating a Tigo Money session."""

    donation_id: UUID = Field(..., description="Internal donation record ID (status: pending)")
    transaction_id: str = Field(..., description="Tigo Money transaction identifier")
    checkout_url: str = Field(..., description="URL to redirect the donor to complete payment")
    amount_pyg: int = Field(..., description="Payment amount in guaraníes")


class TigoCallbackRequest(BaseModel):
    """Webhook payload sent by Tigo Money after payment outcome.

    Field names match the Tigo Money API camelCase format exactly.
    Pydantic model_config allows population by alias as well.
    """

    # Tigo API uses camelCase — noqa: N815 applied per-field (external API names)
    transaction_id: str = Field(
        ..., alias="transactionId", description="Tigo transaction identifier"
    )
    reference: str = Field(..., description="Internal donation ID (UUID string)")
    status: str = Field(..., description="COMPLETED | FAILED | CANCELLED")
    amount: str = Field(..., description="Amount as string (guaraníes, no decimals)")
    merchant_id: str | None = Field(default=None, alias="merchantId")
    timestamp: str | None = Field(default=None)

    model_config = {"populate_by_name": True}

    @field_validator("status")
    @classmethod
    def status_must_be_known(cls, value: str) -> str:
        allowed = {"COMPLETED", "FAILED", "CANCELLED", "PENDING"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"Unknown Tigo status: {value!r}. Expected one of {allowed}")
        return upper
