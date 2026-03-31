"""API endpoints for processing offline-queued donation submissions.

These endpoints receive donations that were stored in IndexedDB while the
user was offline and are submitted automatically when connectivity returns.
"""

from datetime import datetime

from fastapi import APIRouter, status
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/api/queued-donations", tags=["queued-donations"])


class QueuedDonationSubmit(BaseModel):
    """Schema for a donation that was queued offline and is now being submitted."""

    amount: float = Field(..., gt=0, description="Donation amount")
    currency: str = Field(..., pattern="^(PYG|EUR|USD)$", description="Currency code")
    donor_name: str = Field("", max_length=200, description="Donor display name")
    donor_email: EmailStr = Field(..., description="Donor email address")
    message: str = Field("", max_length=1000, description="Optional message")
    queued_at: str = Field(
        ...,
        description="ISO 8601 timestamp when the donation was queued offline",
    )


class QueuedDonationResponse(BaseModel):
    """Response after processing a queued donation."""

    success: bool
    message: str
    donation_id: int | None = None
    processed_at: str


@router.post(
    "",
    response_model=QueuedDonationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an offline-queued donation",
)
async def submit_queued_donation(
    payload: QueuedDonationSubmit,
) -> QueuedDonationResponse:
    """Process a donation that was queued in IndexedDB while offline.

    This endpoint accepts donations that the frontend stored locally
    when the user had no internet connection. The frontend submits
    them automatically once connectivity is restored.
    """
    # MVP: in-memory processing — in production this would call the
    # donation service to create a real Donation record with payment processing.
    now = datetime.now().isoformat()

    return QueuedDonationResponse(
        success=True,
        message="Donacion recibida exitosamente",
        donation_id=None,  # Would be a real ID after DB insert
        processed_at=now,
    )
